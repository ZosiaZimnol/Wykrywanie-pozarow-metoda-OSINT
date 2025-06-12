import praw
import time
import re
import spacy
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app.db.database import get_db_connection
from app.nlp.fire_classifier import is_fire_related
from app.routes.metadata import compute_reliability_score

# Konfiguracja Reddit API
reddit = praw.Reddit(
    client_id="70KphBW1vEavSkGH8vTywg",
    client_secret="CrRvlRrxPZ_D8ZQstRWbP_wOA3cWfA",
    username="Anastasiia_Pashko",
    password="anastasiiaPashko03#",
    user_agent="fire_osint"
)

# Dodajemy subreddity, w tym r/Wildfire gdzie są właśnie informacje o pożarach
SUBREDDITS = ["fire","wildfire","forest fire","firefighter","smokejumper","fire crew","explodes",
              "fire management","fire prevention","fire evacuation","fire hazard","fire season",
              "fire behavior","fire incident","fire suppression","firefighting gear","fire shelter",
              "fire camp","containment","burn severity","evacuation","mop-up","flare-up","fire explosion",
              "injury","death on the job","stress","mental health","pożar","pożary","pożar lasu",
              "strażak","straż pożarna","ogniomistrz","dym","ewakuacja","zagrożenie pożarowe",
              "sezon pożarowy","zarządzanie pożarami","gaszenie pożarów","obóz pożarowy","oparzenia",
              "przeciwdziałanie pożarom","incendio","incendios forestales","bombero","brigada contra incendios",
              "prevención de incendios","gestión de incendios","evacuación","peligro de incendio",
              "temporada de incendios","incendio forestal","contención","supresión de incendios",
              "incendie","feu de forêt","pompier","brigade de pompiers","prévention des incendies",
              "gestion des incendies","évacuation","risque d'incendie","saison des feux","incendie de forêt",
              "confinement","lutte contre les incendies","feuer","waldbrand","feuerwehrmann","feuerwehr",
              "brandbekämpfung","brandschutz","evakuierung","brandgefahr","brandsaison","brandverhalten",
              "einsatzleitung","löschung","incendio","incendio boschivo","vigile del fuoco","brigata antincendio",
              "prevenzione incendi","gestione incendi","evacuazione","pericolo incendio","stagione degli incendi",
              "controllo incendi","spegnimento incendi","пожар","лесной пожар","пожарный","пожарная бригада",
              "предотвращение пожаров","пожарная безопасность","эвакуация","опасность пожара","сезон пожаров",
              "лесной пожар","тушение пожаров","супрессия пожаров","火灾","森林火灾","消防员","灭火","火灾管理",
              "火灾预防","疏散","火灾危险","火灾季节","火灾行为","火灾事故","扑火装备","救火营地","حرائق",
              "حريق الغابات","رجل الإطفاء","فرقة الإطفاء","إدارة الحرائق","الوقاية من الحرائق","الإخلاء",
              "خطر الحريق","موسم الحرائق","سلوك الحريق","حادث الحريق","معدات مكافحة الحرائق","火事",
              "山火事","消防士","消火活動","火災管理","火災予防","避難","火災危険","火災シーズン","火災の挙動",
              "火災事件","消火装備","fogo","incêndio florestal","bombeiro","brigada de incêndio","gestão de incêndios",
              "prevenção de incêndios","evacuação","risco de incêndio","temporada de incêndios","comportamento do fogo",
              "incidente de incêndio","equipamento de combate a incêndio","explosion","blast","detonation","bomb",
              "bombing","bomb threat","explosive","shockwave","shock wave","gas explosion","chemical explosion",
              "accidental explosion","controlled explosion","explosive device","blast radius","secondary explosion",
              "fireball","conflagration","wybuch","eksplozja","bomba","bomby","zagrożenie bombowe","materiał wybuchowy",
              "fala uderzeniowa","odłamki","eksplodować","wybuchowy","wybuch gazu","wybuch chemiczny","wybuch kontrolowany",
              "wybuch niekontrolowany","explosión","detonación","bomba","bombardeo","amenaza de bomba","explosivo",
              "onda expansiva","explosión química","explosión accidental","explosión controlada","dispositivo explosivo",
              "radio de explosión","explosion","détonation","bombe","bombardement","menace de bombe","explosif",
              "onde de choc","explosion chimique","explosion accidentelle","explosion contrôlée","dispositif explosif",
              "rayon d'explosion","explosion","detonation","bombe","bombardierung","bombenalarm","sprengstoff",
              "druckwelle","chemische explosion","unfallexplosion","kontrollierte explosion","sprengsatz",
              "explosionsradius","esplosione","detonazione","bomba","bombardamento","minaccia di bomba","esplosivo",
              "onda d'urto","esplosione chimica","esplosione accidentale","esplosione controllata","dispositivo esplosivo",
              "raggio di esplosione","взрыв","детонация","бомба","бомбёжка","бомбовая угроза","взрывчатое вещество",
              "ударная волна","химический взрыв","несчастный взрыв","контролируемый взрыв","взрывное устройство",
              "радиус взрыва","爆炸","爆裂","炸弹","炸弹威胁","爆炸物","冲击波","化学爆炸","意外爆炸","控制爆炸","爆炸装置",
              "爆炸半径","انفجار","تفجير","قنبلة","تهديد بقنبلة","مواد متفجرة","موجة صدمة","انفجار كيميائي","انفجار عرضي",
              "انفجار مسيطر عليه","جهاز متفجر","نطاق الانفجار","爆発","爆裂","爆弾","爆弾の脅威","爆発物","衝撃波",
              "化学爆発","偶発的爆発","制御爆発","爆発装置","爆発半径","explosão","detonação","bomba","bombardeio",
              "ameaça de bomba","explosivo","onda de choque","explosão química","explosão acidental","explosão controlada",
              "dispositivo explosivo","raio da explosão"]

nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="fire_osint")

CUSTOM_REGION_ALIASES = {
    "Mazowieckie": "Mazowieckie", "Małopolskie": "Małopolskie", "Wielkopolskie": "Wielkopolskie",
    "Śląskie": "Śląskie", "Dolnośląskie": "Dolnośląskie", "Pomorskie": "Pomorskie",
    "Zachodniopomorskie": "Zachodniopomorskie", "Łódzkie": "Łódzkie", "Lubelskie": "Lubelskie",
    "Podkarpackie": "Podkarpackie", "Podlaskie": "Podlaskie", "Kujawsko-Pomorskie": "Kujawsko-Pomorskie",
    "Opolskie": "Opolskie", "Świętokrzyskie": "Świętokrzyskie", "Warmińsko-Mazurskie": "Warmińsko-Mazurskie",
    "Warszawa": "Warsaw", "Kraków": "Krakow", "Wrocław": "Wroclaw", "Łódź": "Lodz",
    "Poznań": "Poznan", "Gdańsk": "Gdansk", "Szczecin": "Szczecin", "Rzeszów": "Rzeszow",
    "CA": "California", "NY": "New York", "TX": "Texas", "Nev.": "Nevada", "NV": "Nevada",
    "FL": "Florida", "IL": "Illinois", "LA": "Los Angeles", "SF": "San Francisco",
    "DC": "Washington, D.C.", "WA": "Washington", "AZ": "Arizona", "UK": "United Kingdom",
    "DE": "Germany", "FR": "France", "PL": "Poland", "ES": "Spain", "UA": "Ukraine",
    "CZ": "Czech Republic", "RU": "Russia", "IN": "India", "CN": "China"
}

def extract_location_candidates(text: str) -> list[str]:
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
    abbreviations = re.findall(r'\b[A-Z]{2,3}\b', text)
    raw_candidates = set(locations + abbreviations)
    normalized = set()

    for loc in raw_candidates:
        cleaned = loc.strip()
        normalized.add(CUSTOM_REGION_ALIASES.get(cleaned, cleaned))
    
    return list(normalized)

def geocode_location(name: str):
    try:
        time.sleep(1)  # Nominatim rate limit
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

    # Sprawdzenie czy lokalizacja już istnieje (w odległości ~100m)
    cur.execute("""
        SELECT id_lok FROM lokalizacja 
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326), 0.001)
    """, (lon, lat))
    result = cur.fetchone()
    if result:
        return result[0]

    # Reverse geocoding aby ustalić województwo
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

    # Pobierz lub utwórz źródło danych Reddit
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

    for sub in SUBREDDITS:
        print(f"Przetwarzanie subreddit: {sub}")
        try:
            for post in reddit.subreddit(sub).new(limit=50):
                title = post.title
                content = post.selftext or ""
                full_text = f"{title} {content}"
                source_url = f"https://www.reddit.com{post.permalink}"
                created = datetime.utcfromtimestamp(post.created_utc).date()

                if not is_fire_related(full_text):
                    continue

                # Sprawdzenie duplikatu
                cur.execute("SELECT 1 FROM pozar WHERE zrodlo_danych = %s", (source_url,))
                if cur.fetchone():
                    continue

                # Wyciąganie lokalizacji
                lokalizacja_id = None
                candidates = extract_location_candidates(full_text)
                for candidate in candidates:
                    lokalizacja_id = get_or_create_location(cur, candidate)
                    if lokalizacja_id:
                        print(f"📍 Lokalizacja znaleziona: '{candidate}', id_lok = {lokalizacja_id}")
                        break

                if lokalizacja_id is None:
                    print(f"❌ Brak lokalizacji dla posta: {source_url}, pomijam wpis do bazy.")
                    continue  # pomijamy post bez lokalizacji

                # Oblicz wiarygodność na podstawie score i liczby komentarzy
                reliability = compute_reliability_score(post.score, post.num_comments)

                # Dodanie rekordu pożaru
                cur.execute("""
                    INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id_pozaru
                """, (created, title[:1000], source_url, reliability, lokalizacja_id))
                pozar_id = cur.fetchone()[0]

                # Dodanie raportu
                cur.execute("""
                    INSERT INTO raport (tekst, data_publikacji, autor, pozar_id_pozaru, zrodla_danych_id_zr)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    content[:4000] if content else title[:4000],
                    created,
                    str(post.author.name)[:100] if post.author else "anon",
                    pozar_id,
                    zrodlo_id
                ))

                conn.commit()
                print(f"✅ Dodano post: {title}")

        except Exception as e:
            print(f"❌ Błąd w subreddicie {sub}: {e}")
            conn.rollback()
            continue

    cur.close()
    conn.close()

if __name__ == "__main__":
    scrape_and_store_posts()
    print("✅ Scraping zakończony!")
