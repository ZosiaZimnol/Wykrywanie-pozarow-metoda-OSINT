import os
import csv
import requests
from io import StringIO
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app.db.database import get_db_connection

NASA_API_KEY = os.getenv("NASA_API_KEY", "c378bbd852a1e124cec4a8890f11160d")
NASA_URL = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_API_KEY}/MODIS_NRT/world/1"

geolocator = Nominatim(user_agent="fire_osint")

def compute_nasa_reliability(confidence: int, frp: float, daynight: str) -> float:
    score = 0.0
    if confidence >= 80:
        score += 0.6
    elif confidence >= 50:
        score += 0.4
    else:
        score += 0.2

    if frp >= 30:
        score += 0.3
    elif frp >= 15:
        score += 0.2
    else:
        score += 0.1

    if daynight.upper() == "D":
        score += 0.1

    return round(min(score, 1.0), 2)

def classify_threat(wiarygodnosc: float) -> str:
    if wiarygodnosc >= 0.8:
        return "wysoka"
    elif wiarygodnosc >= 0.5:
        return "średnia"
    else:
        return "mała"

def fetch_and_store_nasa_fires():
    print(f"📡 Pobieram dane z NASA: {NASA_URL}")
    response = requests.get(NASA_URL)
    if response.status_code != 200:
        print(f"❌ Błąd pobierania danych z NASA: {response.status_code}")
        return

    csv_data = response.text
    csv_reader = csv.DictReader(StringIO(csv_data))

    conn = get_db_connection()
    cur = conn.cursor()

    # Zapisz źródło danych NASA
    cur.execute("SELECT id_zr FROM zrodla_danych WHERE nazwa = 'NASA FIRMS'")
    zr = cur.fetchone()
    if zr:
        nasa_zrodlo_id = zr[0]
    else:
        cur.execute("""
            INSERT INTO zrodla_danych (nazwa, typ, adres_url, metoda_dostepu)
            VALUES ('NASA FIRMS', 'satelita', %s, 'API') RETURNING id_zr
        """, (NASA_URL,))
        nasa_zrodlo_id = cur.fetchone()[0]
        conn.commit()

    count = 0
    for row in csv_reader:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            confidence = int(row.get('confidence', 0))
            frp = float(row.get('frp', 0.0))
            daynight = row.get('daynight', 'N')

            wiarygodnosc = compute_nasa_reliability(confidence, frp, daynight)
            ocena = classify_threat(wiarygodnosc)

            address = "NASA FIRMS"
            wojewodztwo = "Nieznane"
            try:
                location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
                if location and location.address:
                    address = location.address
                    if location.raw and 'address' in location.raw:
                        address_data = location.raw['address']
                        wojewodztwo = (
                            address_data.get('state') or
                            address_data.get('province') or
                            address_data.get('region') or
                            address_data.get('state_district') or
                            address_data.get('county') or
                            address_data.get('country', 'Nieznane')
                        )
            except (GeocoderTimedOut, GeocoderServiceError) as geo_err:
                print(f"⚠️ Błąd geolokalizacji: {geo_err}")

            cur.execute("""
                INSERT INTO lokalizacja (geom, adres_opisowy, wojewodztwo)
                VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                RETURNING id_lok
            """, (lon, lat, address[:255], wojewodztwo))
            lokalizacja_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_pozaru
            """, (
                datetime.utcnow().date(),
                "Pożar wykryty przez satelitę NASA FIRMS",
                NASA_URL,
                wiarygodnosc,
                lokalizacja_id
            ))
            pozar_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO raport (tekst, data_publikacji, autor, pozar_id_pozaru, zrodla_danych_id_zr)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                f"NASA wykryła pożar o wiarygodności {wiarygodnosc}, zagrożenie: {ocena}. Lokalizacja: {address[:255]}",
                datetime.utcnow().date(),
                "NASA-FIRMS",
                pozar_id,
                nasa_zrodlo_id
            ))

            conn.commit()
            count += 1
            print(f"✅ Dodano pożar z raportem: {address} ({lat}, {lon}) - wiarygodność: {wiarygodnosc}")

        except Exception as e:
            print(f"❌ Błąd: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print(f"✅ Dodano {count} pożarów z NASA z raportami.")
