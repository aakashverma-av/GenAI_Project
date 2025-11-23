import json
from faker import Faker
import random
import os
fake = Faker()
os.makedirs('./data', exist_ok=True)

diagnoses = ["Chronic Kidney Disease Stage 3", "Acute Kidney Injury", "Nephrotic Syndrome", "Hypertensive Nephropathy"]
meds_pool = [
    ["Lisinopril 10mg daily", "Furosemide 20mg twice daily"],
    ["Amlodipine 5mg daily", "Metoprolol 50mg daily"],
    ["Prednisone 10mg daily"],
    ["Losartan 50mg daily", "Atorvastatin 20mg nightly"]
]

patients = []
for i in range(30):
    name = fake.name()
    p = {
        "patient_name": name,
        "discharge_date": fake.date_between(start_date='-180d', end_date='today').isoformat(),
        "primary_diagnosis": random.choice(diagnoses),
        "medications": random.choice(meds_pool),
        "dietary_restrictions": "Low sodium (2g/day), fluid restriction (1.5L/day)",
        "follow_up": "Nephrology clinic in 2 weeks",
        "warning_signs": "Swelling, shortness of breath, decreased urine output",
        "discharge_instructions": "Monitor blood pressure daily, weigh yourself daily"
    }
    patients.append(p)

with open('./data/patients.json', 'w', encoding='utf-8') as f:
    json.dump(patients, f, indent=2)

print("Generated patients.json with", len(patients))
