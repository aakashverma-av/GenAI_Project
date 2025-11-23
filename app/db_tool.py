import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from app.logger_conf import logger

DB_PATH = os.getenv("SQLITE_DB_PATH", "../data/patients.db")

def init_db(json_path: str = "../data/patients.json"):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        data JSON
    )
    """)
    conn.commit()

    # load JSON sample patients
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            patients = json.load(f)
        for p in patients:
            try:
                c.execute("INSERT INTO patients (patient_name, data) VALUES (?, ?)",
                          (p.get("patient_name"), json.dumps(p)))
            except Exception as e:
                logger.exception("Error inserting patient: %s", e)
        conn.commit()
        logger.info("Loaded sample patients into DB.")
    conn.close()

def lookup_patient_by_name(name: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, patient_name, data FROM patients WHERE LOWER(patient_name) = ?", (name.lower(),))
        rows = c.fetchall()
        if not rows:
            # try fuzzy match substring
            c.execute("SELECT id, patient_name, data FROM patients WHERE LOWER(patient_name) LIKE ?", (f"%{name.lower()}%",))
            rows = c.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "patient_name": r[1],
                "data": json.loads(r[2])
            })
        logger.info("DB lookup for '%s' returned %d results", name, len(results))
        return results
    except Exception as e:
        logger.exception("DB lookup error: %s", e)
        return []
    finally:
        conn.close()
