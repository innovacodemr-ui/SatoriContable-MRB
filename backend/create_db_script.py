import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to the default 'postgres' database to create the new one
    try:
        conn = psycopg2.connect(
            user="postgres",
            password="Mario",
            host="localhost",
            port="5432",
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'satori_db'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute("CREATE DATABASE satori_db")
            print("Base de datos 'satori_db' creada exitosamente.")
        else:
            print("La base de datos 'satori_db' ya existe.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al conectar o crear la base de datos: {e}")
        # If connection fails, maybe the server is not running or creds are wrong
        # We'll just print the error and let the user handle it if it fails.

if __name__ == "__main__":
    create_database()
