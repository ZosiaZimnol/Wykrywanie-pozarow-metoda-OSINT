import praw
from datetime import datetime
from app.db.database import get_db_connection
from app.nlp.fire_classifier import is_fire_related

reddit = praw.Reddit(
    client_id="70KphBW1vEavSkGH8vTywg",
    client_secret="CrRvlRrxPZ_D8ZQstRWbP_wOA3cWfA",
    username="Anastasiia_Pashko",
    password="anastasiiaPashko03#",
    user_agent="fire_osint"
)

SUBREDDITS = ["fire", "wildfire", "naturaldisasters"]

def scrape_and_store_posts():
    conn = get_db_connection()
    cur = conn.cursor()

    # Pobierz lub utwórz źródło danych "Reddit"
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
        subreddit = reddit.subreddit(sub)
        for post in subreddit.hot(limit=10):
            title = post.title
            content = post.selftext
            source_url = f"https://www.reddit.com{post.permalink}"
            created = datetime.utcfromtimestamp(post.created_utc).date()

            # NLP - filtrujemy posty niezwiązane z pożarami
            if not is_fire_related(f"{title} {content}"):
                continue

            # Sprawdź, czy URL już istnieje w tabeli 'pozar' (kolumna zrodlo_danych to URL)
            cur.execute("SELECT 1 FROM pozar WHERE zrodlo_danych = %s", (source_url,))
            if cur.fetchone():
                continue

            # Wstawiamy nowy wpis do pozar (lokalizacja NULL bo jeszcze nie mamy danych)
            cur.execute("""
                INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok)
                VALUES (%s, %s, %s, %s, NULL) RETURNING id_pozaru
            """, (created, title[:1000], source_url, 0.85))
            pozar_id = cur.fetchone()[0]

            # Wstawiamy raport powiązany z pożarem i źródłem danych
            cur.execute("""
                INSERT INTO raport (tekst, data_publikacji, autor, pozar_id_pozaru, zrodla_danych_id_zr)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                content[:4000],
                created,
                post.author.name if post.author else "anon",
                pozar_id,
                zrodlo_id
            ))

            conn.commit()

    cur.close()
    conn.close()
