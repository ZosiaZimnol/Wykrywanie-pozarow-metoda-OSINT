from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.routes import test
from app.routes.reddit_scraper import scrape_and_store_posts
from app.routes.nasa_scraper import fetch_and_store_nasa_fires
from app.db.database import get_db_connection
from app.routes import reddit_scraper, nasa_scraper

app = FastAPI()

# Middleware CORS (dla frontendów lokalnych)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Możesz zawęzić np. do ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
app.include_router(test.router)
print("✅ ROUTER ZOSTAŁ ZAŁADOWANy")

# 🔘 Endpoint wywoływany przyciskiem „Aktualizuj”
@app.post("/aktualizuj")
def run_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(scrape_and_store_posts)
    background_tasks.add_task(fetch_and_store_nasa_fires)
    return {"status": "Aktualizacja rozpoczęta"}

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
