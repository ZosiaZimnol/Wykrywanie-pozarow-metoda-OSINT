import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        dbname="fire-osint",
        user="root",
        password="root",
        host="localhost",
        port="5432"
    )
    conn.set_client_encoding('UTF8')
    return conn
