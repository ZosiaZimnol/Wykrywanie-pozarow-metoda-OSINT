from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import test
from app.routes.reddit_scraper import scrape_and_store_posts
from app.db.database import get_db_connection
from app.routes.nasa_scraper import fetch_and_store_nasa_fires
import threading
import time


app = FastAPI()

# Middleware CORS (dla frontendów lokalnych)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Możesz ograniczyć do frontendu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
app.include_router(test.router)
print("✅ ROUTER ZOSTAŁ ZAŁADOWANy")

@app.get("/")
async def root():
    return {"message": "API działa poprawnie"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/ping-db")
async def ping_db():
    try:
        print("🔄 Próba połączenia z bazą danych...")
        conn = get_db_connection()
        print("✅ Połączono z bazą.")
        cur = conn.cursor()
        cur.execute("SELECT * FROM lokalizacja LIMIT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db": "ok", "result": result}
    except Exception as e:
        print(f"❌ Błąd połączenia z DB: {e}")
        return {"db": "error", "details": str(e)}

@app.get("/pozar-count")
def count_pozary():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pozar;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"count": count}

# Funkcja uruchamiająca scraper okresowo
def periodic_scrape(interval_seconds=60):
    while True:
        print("🔁 Automatyczne pobieranie danych z Reddita i NASA...")
        try:
            scrape_and_store_posts()
            print("✅ Dane z Reddita zostały zapisane.")
        except Exception as e:
            print(f"❌ Błąd scrapera Reddit: {e}")
        try:
            fetch_and_store_nasa_fires()
            print("✅ Dane z NASA zostały zapisane.")
        except Exception as e:
            print(f"❌ Błąd scrapera NASA: {e}")
        time.sleep(interval_seconds)


@app.on_event("startup")
def start_background_scraper():
    threading.Thread(target=periodic_scrape, daemon=True).start()
