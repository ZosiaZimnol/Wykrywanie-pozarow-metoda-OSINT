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

    # Dodaj źródło danych (jeśli nie istnieje)
    cur.execute("SELECT id_zr FROM zrodla_danych WHERE nazwa = 'Reddit'")
    result = cur.fetchone()
    if result:
        zrodlo_id = result[0]
    else:
        cur.execute("""
            INSERT INTO zrodla_danych (nazwa, typ, adres_url, metoda_dostepu)
            VALUES (%s, %s, %s, %s) RETURNING id_zr
        """, ('Reddit', 'media społecznościowe', 'https://www.reddit.com', 'API'))
        zrodlo_id = cur.fetchone()[0]

    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).hot(limit=10):
            title = post.title
            content = post.selftext
            source_url = f"https://www.reddit.com{post.permalink}"
            created = datetime.utcfromtimestamp(post.created_utc).date()

            # 🔍 Klasyfikacja NLP – czy to post o pożarze?
            if not is_fire_related(f"{title} {content}"):
                continue

            # 🛡️ Duplikat?
            cur.execute("SELECT 1 FROM pozar WHERE zrodlo_danych = %s", (source_url,))
            if cur.fetchone():
                continue

            # 🔥 Zapis do pozar (bez lokalizacji, na razie NULL)
            cur.execute("""
                INSERT INTO pozar (data_wykrycia, opis, zrodlo_danych, wiarygodnosc, lokalizacja_id_lok)
                VALUES (%s, %s, %s, %s, NULL) RETURNING id_pozaru
            """, (created, title[:1000], source_url, 0.85))
            pozar_id = cur.fetchone()[0]

            # 📝 Zapis do raport
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