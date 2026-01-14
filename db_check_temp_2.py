import psycopg2
import sys

print("Checking DB connection Round 2...")
try:
    conn = psycopg2.connect(dbname='satori_db', user='satori_user', password='satori_pass', host='db')
    print("SUCCESS: satori_db + satori_pass")
    conn.close()
except Exception as e:
    print(f"FAIL: satori_db + satori_pass - {e}")
