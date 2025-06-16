import os
import csv
import requests
from io import StringIO
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app.db.database import get_db_connection


# Klucz API i URL pobierania
NASA_API_KEY = os.getenv("NASA_API_KEY", "c378bbd852a1e124cec4a8890f11160d")
NASA_URL = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_API_KEY}/MODIS_NRT/world/1"

# Inicjalizacja geolokalizatora
geolocator = Nominatim(user_agent="fire_osint")

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

            # Reverse geocoding
            address = "NASA FIRMS"
            wojewodztwo = "Nieznane"

            try:
                location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
                if location and location.address:
                    address = location.address

                    # Ustal województwo/provincję/region
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

            # Zapis do bazy danych
            try:
                # Wstawienie do tabeli lokalizacja
                cur.execute("""
                    INSERT INTO lokalizacja (geom, adres_opisowy, wojewodztwo)
                    VALUES (
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                        %s,
                        %s
                    )
                    RETURNING id_lok;
                """, (lon, lat, address, wojewodztwo))
                
                lokalizacja_id = cur.fetchone()[0]

                # Wstawienie do tabeli pozar z linkiem do źródła danych
                cur.execute("""
                    INSERT INTO pozar (
                        data_wykrycia, 
                        opis, 
                        zrodlo_danych, 
                        wiarygodnosc, 
                        lokalizacja_id_lok
                    )
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    datetime.utcnow().date(),
                    "Pożar wykryty przez satelitę NASA FIRMS",
                    NASA_URL,  # ← zapisujemy źródło danych
                    0.9,
                    lokalizacja_id
                ))

                conn.commit()
                count += 1
                print(f"✅ Dodano pożar: {address} ({lat}, {lon})")

            except Exception as db_err:
                conn.rollback()
                print(f"❌ Błąd bazy danych: {db_err}")
                print(f"🔍 Problem z wierszem: {row}")

        except Exception as parse_err:
            print(f"❌ Błąd przetwarzania: {parse_err}")
            print(f"🔍 Problem z wierszem: {row}")
    


    cur.close()
    conn.close()
    print(f"✅ Zakończono import. Dodano {count} nowych pożarów.")

def update_nasa_data():
    print("🔁 Aktualizacja danych z NASA...")
    fetch_and_store_nasa_fires()
    print("✅ NASA scraping zakończony.")
