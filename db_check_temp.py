import psycopg2
import sys

print("Checking DB connection...")
try:
    conn = psycopg2.connect(dbname='satori_prod', user='satori_user', password='satori_pass', host='db')
    print("SUCCESS: satori_pass")
    conn.close()
except Exception as e:
    print(f"FAIL: satori_pass - {e}")

try:
    conn = psycopg2.connect(dbname='satori_prod', user='satori_user', password='satori_strong_password', host='db')
    print("SUCCESS: satori_strong_password")
    conn.close()
except Exception as e:
    print(f"FAIL: satori_strong_password - {e}")
