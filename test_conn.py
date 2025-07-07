# test_conn.py
from db import get_connection

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE()")
    print("Koneksi berhasil. Waktu sekarang:", cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print("Koneksi gagal:", e)
