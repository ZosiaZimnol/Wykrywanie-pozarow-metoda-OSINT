from fastapi import APIRouter
from app.db.database import get_db_connection

router = APIRouter()

@router.get("/test-db")
async def test_database_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id_lok, adres_opisowy, wojewodztwo FROM lokalizacja;")
        rows = cur.fetchall()
        conn.close()

        result = [
            {
                "id_lok": row[0],
                "adres_opisowy": row[1],
                "wojewodztwo": row[2]
            }
            for row in rows
        ]

        return {"message": "Połączenie OK!", "dane": result}
    except Exception as e:
        return {"message": f"Błąd połączenia: {str(e)}"}
