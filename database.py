import sqlite3

DATABASE = "data_telur.db"

def koneksi():
    return sqlite3.connect(DATABASE, check_same_thread=False)

conn = koneksi()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produksi(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    ayam INTEGER,
    bebek INTEGER,
    puyuh INTEGER
)
""")

conn.commit()