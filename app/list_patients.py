import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB = os.getenv("SQLITE_DB_PATH", "./data/patients.db")

print("Inspecting DB:", DB)

if not os.path.exists(DB):
    print("DB does not exist at:", DB)
else:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        rows = c.execute("SELECT id, patient_name FROM patients ORDER BY id LIMIT 200").fetchall()
        if rows:
            print("\n--- Patients in DB ---")
            for r in rows:
                print(r)
        else:
            print("\nNo rows found in table 'patients'.")
    except Exception as e:
        print("\nError reading DB:", e)
    finally:
        conn.close()
