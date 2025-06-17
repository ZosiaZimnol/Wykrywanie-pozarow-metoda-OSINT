import praw
import time
import re
import spacy
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app.db.database import get_db_connection
from app.nlp.fire_classifier import is_fire_related, FIRE_KEYWORDS, SUBREDDIT_NAMES, CUSTOM_REGION_ALIASES
from app.routes.metadata import compute_reliability_score

# Konfiguracja Reddit API
reddit = praw.Reddit(
    client_id="70KphBW1vEavSkGH8vTywg",
    client_secret="CrRvlRrxPZ_D8ZQstRWbP_wOA3cWfA",
    username="Anastasiia_Pashko",
    password="anastasiiaPashko03#",
    user_agent="fire_osint"
)

nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="fire_osint")


def ocena_zagrozenia_reddit(upvotes: int, comments: int, tekst: str) -> str:
    score = 0

    if upvotes > 50:
        score += 1
    if comments > 20:
        score += 1

    tekst = tekst.lower()
    keywords_high = ["ewakuacja", "wielki pożar", "płonie całe", "zginęli", "ognia nie da się opanować"]
    keywords_medium = ["płonie", "duży ogień", "strażacy", "gaszą", "płomienie"]

    if any(word in tekst for word in keywords_high):
        score += 2
    elif any(word in tekst for word in keywords_medium):
        score += 1

    if score >= 3:
        return "wysoka"
    elif score == 2:
        return "średnia"
    else:
        return "mała"


def is_financial_post(text: str) -> bool:
    money_patterns = [
        r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?",
        r"\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s?(USD|usd|dollars|bucks)",
        r"\b(FIRE|CoastFIRE|LeanFIRE|FatFIRE)\b",
        r"\b(retire|retirement|investment|portfolio|net worth|assets|savings|financial independence)\b",
        r"\b(inwestycje|emerytura|oszczędności|kapitał|majątek)\b"
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in money_patterns)


def extract_location_candidates(text: str) -> list[str]:
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
    abbreviations = re.findall(r'\b[A-Z]{2,3}\b', text)
    raw_candidates = set(locations + abbreviations)
    return list({CUSTOM_REGION_ALIASES.get(loc.strip(), loc.strip()) for loc in raw_candidates})


def geocode_location(name: str):
    try:
        time.sleep(1)
        return geolocator.geocode(name, timeout=10)
    except GeocoderTimedOut:
        return geocode_location(name)


def reverse_location(lat: float, lon: float):
    try:
        time.sleep(1)
        return geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError):
        return None


def get_or_create_location(cur, location_text: str):
    loc = geocode_location(location_text)
    if not loc:
        return None

    lat, lon = loc.latitude, loc.longitude
    address = loc.address or location_text

    cur.execute("""
        SELECT id_lok FROM lokalizacja 
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326), 0.001)
    """, (lon, lat))
    result = cur.fetchone()
    if result:
        return result[0]

    reverse = reverse_location(lat, lon)
    woj = reverse.raw['address'].get('state', 'Nieznane') if reverse else 'Nieznane'

    cur.execute("""
        INSERT INTO lokalizacja (geom, adres_opisowy, wojewodztwo)
        VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
        RETURNING id_lok
    """, (lon, lat, address[:255], woj))

    return cur.fetchone()[0]


def scrape_and_store_posts():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id_zr FROM zrodla_danych WHERE nazwa = %s", ('Reddit',))
    result = cur.fetchone()
    if result:
        zrodlo_id = result[0]
    else:
        cur.execute("""
            INSERT INTO zrodla_danych (nazwa, typ, adres_url, metoda_dostepu)
            VALUES (%s, %s, %s, %s) RETURNING id_zr
        """, ('Reddit', 'media społecznościowe', 'https://www.reddit.com', 'API'))
        zrodlo_id = cur.fetchone()[0]
        conn.commit()

    for sub in SUBREDDIT_NAMES:
        print(f"Przetwarzanie subreddit: {sub}")
        try:
            for post in reddit.subreddit(sub).new(limit=50):
                title = post.title
                content = post.selftext or ""
                full_text = f"{title} {content}".lower()
                source_url = f"https://www.reddit.com{post.permalink}"
                created = datetime.utcfromtimestamp(post.created_utc).date()

                if not is_fire_related(full_text):
                    continue

                if is_financial_post(full_text):
                    print(f"💸 Pominięto post o charakterze finansowym: {source_url}")
                    continue

                cur.execute("""
                    SELECT 1 FROM pozar 
                    WHERE zrodlo_danych = %s OR (opis = %s AND data_wykrycia = %s)
                """, (source_url, title[:1000], created))
                if cur.fetchone():
                    continue

                lokalizacja_id = None
                for candidate in extract_location_candidates(full_text):
                    lokalizacja_id = get_or_create_location(cur, candidate)
                    if lokalizacja_id:
                        print(f"📍 Lokalizacja znaleziona: '{candidate}', id_lok = {lokalizacja_id}")
                        break

                if lokalizacja_id is None:
                    print(f"❌ Brak lokalizacji dla posta: {source_url}")
                    continue

                reliability = compute_reliability_score(post.score, post.num_comments)
                ocena = ocena_zagrozenia_reddit(post.score, post.num_comments, full_text)

                cur.execute("""
                    INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok, ocena_zagrozenia)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_pozaru
                """, (created, title[:1000], source_url, reliability, lokalizacja_id, ocena))
                pozar_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO raport (tekst, data_publikacji, autor, pozar_id_pozaru, zrodla_danych_id_zr)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    content[:1000] if content else title[:1000],
                    created,
                    str(post.author.name)[:100] if post.author else "anon",
                    pozar_id,
                    zrodlo_id
                ))

                conn.commit()
                print(f"✅ Dodano post: {title} (ocena zagrożenia: {ocena})")

        except Exception as e:
            print(f"❌ Błąd w subreddicie {sub}: {e}")
            conn.rollback()

    cur.close()
    conn.close()


def update_reddit_data():
    print("🔁 Aktualizacja danych z Reddita...")
    scrape_and_store_posts()
    print("✅ Reddit scraping zakończony.")
