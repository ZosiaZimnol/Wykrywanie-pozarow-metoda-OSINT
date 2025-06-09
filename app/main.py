from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import test
from app.db.database import get_db_connection


app = FastAPI()

# Middleware CORS (dla frontendów lokalnych)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Możesz ograniczyć np. do ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router testowy
app.include_router(test.router)
print("✅ ROUTER TEST ZOSTAŁ ZAŁADOWANY")


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
        cur.execute("SELECT * FROM lokalizacja;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db": "ok", "result": result}
    except Exception as e:
        print(f"❌ Błąd połączenia z DB: {e}")
        return {"db": "error", "details": str(e)}
