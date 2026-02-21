import sqlite3
import os

db_files = [f for f in os.listdir('.') if f.endswith('.db')]
for db in db_files:
    print(f"--- DB: {db} ---")
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for t in tables:
            print(f"Table: {t[0]}")
            cols = cursor.execute(f"PRAGMA table_info({t[0]})").fetchall()
            for c in cols:
                print(f"  Col: {c[1]} ({c[2]})")
            data = cursor.execute(f"SELECT * FROM {t[0]} LIMIT 2").fetchall()
            print(f"  Data: {data}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
