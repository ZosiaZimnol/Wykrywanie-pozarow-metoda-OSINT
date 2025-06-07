from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import test


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
