import os
import re
import requests
import pdfplumber
import spacy
from datetime import datetime
from bs4 import BeautifulSoup
from app.db.database import get_db_connection

nlp = spacy.load("en_core_web_sm")

PDF_DIR = "app/static/nifc_reports"
BASE_URL = "https://www.nifc.gov/nicc/predictive-services/intelligence"
os.makedirs(PDF_DIR, exist_ok=True)

# Heurystyka dla oceny zagrożenia
def classify_threat_from_description(desc: str) -> str:
    desc_lower = desc.lower()
    if any(word in desc_lower for word in ["extreme", "out of control", "emergency", "rapid spread"]):
        return "wysoka"
    elif any(word in desc_lower for word in ["contained", "controlled", "monitoring", "low intensity"]):
        return "niska"
    else:
        return "średnia"

def get_pdf_links():
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".pdf") and "complete" in a.text.lower():
            full_url = href if href.startswith("http") else "https://www.nifc.gov" + href
            links.append(full_url)
    return links

def download_pdf(url):
    filename = os.path.join(PDF_DIR, os.path.basename(url))
    if not os.path.exists(filename):
        r = requests.get(url)
        with open(filename, "wb") as f:
            f.write(r.content)
    return filename

def extract_data(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    # Data publikacji z raportu
    date_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", text)
    report_date = datetime.strptime(date_match.group(), "%B %Y").date() if date_match else datetime.utcnow().date()

    doc = nlp(text)
    fire_entries = [sent.text.strip() for sent in doc.sents if "fire" in sent.text.lower()][:2]

    results = []
    for fragment in fire_entries:
        frag_doc = nlp(fragment)
        locations = list(set(ent.text for ent in frag_doc.ents if ent.label_ == "GPE"))
        location = locations[0] if locations else None

        ocena = classify_threat_from_description(fragment)
        wiarygodnosc = 0.9  # stała dla NIFC

        results.append({
            "data_publikacji": report_date,
            "lokalizacja": location,
            "tekst": fragment,
            "opis": fragment[:200],
            "wiarygodnosc": wiarygodnosc,
            "ocena_zagrozenia": ocena
        })

    return results

def fetch_and_store_nifc_reports():
    links = get_pdf_links()
    conn = get_db_connection()
    cur = conn.cursor()

    for url in links:
        try:
            path = download_pdf(url)
            entries = extract_data(path)

            # Dodaj źródło danych
            cur.execute("INSERT INTO zrodla_danych (nazwa, typ, adres_url, metoda_dostepu) VALUES (%s, %s, %s, %s) RETURNING id_zr",
                        ("NIFC Weekly Report", "PDF", url, "scraper"))
            id_zr = cur.fetchone()[0]

            for data in entries:
                lok_id = None
                if data["lokalizacja"]:
                    cur.execute("INSERT INTO lokalizacja (adres_opisowy, wojewodztwo, geom) VALUES (%s, %s, ST_SetSRID(ST_MakePoint(0,0),4326)) RETURNING id_lok",
                                (data["lokalizacja"], data["lokalizacja"]))
                    lok_id = cur.fetchone()[0]

                cur.execute("INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok, ocena_zagrozenia) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_pozaru",
                            (data["data_publikacji"], data["opis"], "NIFC", data["wiarygodnosc"], lok_id, data["ocena_zagrozenia"]))
                id_pozar = cur.fetchone()[0]

                cur.execute("INSERT INTO raport (tekst, data_publikacji, autor, pozar_id_pozaru, zrodla_danych_id_zr) VALUES (%s, %s, %s, %s, %s)",
                            (data["tekst"], data["data_publikacji"], "NIFC", id_pozar, id_zr))

            print(f"✅ Zapisano {len(entries)} pożarów z raportu {url}")
            conn.commit()

        except Exception as e:
            print(f"❌ Błąd przy {url}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
