# app/routes/nasa_scraper.py

import os
import csv
import requests
from io import StringIO
from datetime import datetime
from app.db.database import get_db_connection

# Klucz z .env lub na sztywno
NASA_API_KEY = os.getenv("NASA_API_KEY", "c378bbd852a1e124cec4a8890f11160d")

# GLOBALNY endpoint (MODIS, 24h)
NASA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/c378bbd852a1e124cec4a8890f11160d/MODIS_NRT/world/1"


def fetch_and_store_nasa_fires():
    print(f"📡 Pobieram dane z NASA: {NASA_URL}")
    response = requests.get(NASA_URL)

    if response.status_code != 200:
        print(f"❌ Błąd pobierania danych z NASA: {response.status_code}")
        return

    csv_data = response.text
    print("📄 PODGLĄD CSV (pierwsze 500 znaków):")
    print(csv_data[:500])

    csv_reader = csv.DictReader(StringIO(csv_data))

    conn = get_db_connection()
    cur = conn.cursor()

    count = 0
    for row in csv_reader:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            acq_date = datetime.strptime(row['acq_date'], "%Y-%m-%d").date()
            confidence = float(row.get('confidence', 0))
            description = f"NASA fire data (brightness: {row.get('brightness', '')})"

            # Sprawdź, czy taki punkt już istnieje
            cur.execute("""
                SELECT id_lok FROM lokalizacja 
                WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326), 0.0005)
            """, (lon, lat))
            existing = cur.fetchone()

            if existing:
                id_lok = existing[0]
            else:
                cur.execute("""
                    INSERT INTO lokalizacja (geom, adres_opisowy, wojewodztwo)
                    VALUES (ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                    RETURNING id_lok
                """, (lon, lat, "NASA FIRMS", "Nieznane"))
                id_lok = cur.fetchone()[0]

            # Dodaj pożar
            cur.execute("""
                INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok)
                VALUES (%s, %s, %s, %s, %s)
            """, (acq_date, description[:1000], "NASA FIRMS", confidence / 100, id_lok))

            count += 1

        except Exception as e:
            print(f"❌ Błąd przetwarzania wiersza: {e}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Zakończono zapis danych NASA. Dodano: {count} rekordów.")
