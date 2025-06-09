import psycopg2
import time

def get_db_connection(retries=5, delay=3):
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                dbname="fire-osint",
                user="root",
                password="root",
                host="db",
                port="5432"
            )
            conn.set_client_encoding('UTF8')
            return conn
        except psycopg2.OperationalError as e:
            print(f"❌ Próba {i+1} nieudana: {e}")
            time.sleep(delay)
    raise Exception("Nie udało się połączyć z bazą danych po kilku próbach.")
