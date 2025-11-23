import sqlite3, json, os
from dotenv import load_dotenv
load_dotenv()

# Use env path if present else default to project-root/data/patients.db
DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/patients.db")
JSON_PATH = os.getenv("PATIENTS_JSON_PATH", "./data/patients.json")

print("Project working dir:", os.getcwd())
print("DB will be created at:", DB_PATH)
print("JSON source:", JSON_PATH)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if not os.path.exists(JSON_PATH):
    raise SystemExit(f"ERROR: patients.json not found at {JSON_PATH}. Run your patient generator first.")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    data TEXT
);
""")
conn.commit()

with open(JSON_PATH, "r", encoding="utf-8") as f:
    patients = json.load(f)

inserted = 0
for p in patients:
    pname = p.get("patient_name", "").strip()
    if not pname:
        continue
    # avoid duplicates
    cur = c.execute("SELECT COUNT(1) FROM patients WHERE patient_name = ?", (pname,)).fetchone()
    if cur and cur[0] > 0:
        continue
    c.execute("INSERT INTO patients (patient_name, data) VALUES (?, ?)", (pname, json.dumps(p)))
    inserted += 1

conn.commit()
conn.close()
print(f"Done. Inserted {inserted} records into {DB_PATH}")
