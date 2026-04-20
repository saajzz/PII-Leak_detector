import sys, os
sys.path.append(os.path.dirname(__file__))

from database import get_connection, init_db
from datetime import datetime, timezone, timedelta
import random

DEMO_INCIDENTS = [
    {"source_url": "https://pastebin.com/xK9mP2qR",   "source_type": "pastebin",       "severity": "Critical", "score": 10, "pii_types": "aadhaar, pan, mobile, upi", "record_count": 847, "hours_ago": 1},
    {"source_url": "https://github.com/anon-leaks/india-users/blob/main/dump.csv", "source_type": "github_search", "severity": "Critical", "score": 10, "pii_types": "aadhaar, pan, mobile", "record_count": 1243, "hours_ago": 3},
    {"source_url": "https://pastebin.com/Tz3nW8vL",   "source_type": "pastebin",       "severity": "High",     "score": 8,  "pii_types": "aadhaar, mobile",           "record_count": 312, "hours_ago": 5},
    {"source_url": "https://controlc.com/a7f29e11",   "source_type": "controlc",       "severity": "Critical", "score": 10, "pii_types": "aadhaar, pan, upi, ifsc",   "record_count": 2100,"hours_ago": 7},
    {"source_url": "https://github.com/data-breach/ration-card-ap/blob/main/list.txt","source_type": "github_search","severity": "High","score": 7,"pii_types": "aadhaar, mobile","record_count": 589,"hours_ago": 12},
    {"source_url": "https://pastebin.com/mQ4xR9sY",   "source_type": "pastebin",       "severity": "Medium",   "score": 5,  "pii_types": "mobile, email_in",          "record_count": 134, "hours_ago": 18},
    {"source_url": "https://paste.fo/7c3a912b",        "source_type": "paste_fo",       "severity": "Critical", "score": 9,  "pii_types": "aadhaar, pan, mobile",      "record_count": 421, "hours_ago": 22},
    {"source_url": "https://github.com/leaked-db/cowin-data/blob/main/beneficiaries.json","source_type": "github_search","severity": "High","score": 8,"pii_types": "aadhaar, mobile, email_in","record_count": 3847,"hours_ago": 30},
    {"source_url": "https://controlc.com/f8b12d45",   "source_type": "controlc",       "severity": "Medium",   "score": 4,  "pii_types": "pan, email_in",             "record_count": 67,  "hours_ago": 36},
    {"source_url": "https://pastebin.com/hN7kL3pM",   "source_type": "pastebin",       "severity": "Low",      "score": 2,  "pii_types": "email_in",                  "record_count": 28,  "hours_ago": 48},
    {"source_url": "https://github.com/anon/railway-pnr-leak/blob/main/dump.sql",  "source_type": "github_search","severity": "Critical","score": 10,"pii_types": "aadhaar, pan, mobile, upi, ifsc","record_count": 5621,"hours_ago": 60},
    {"source_url": "https://paste.fo/2e9f4c78",        "source_type": "paste_fo",       "severity": "High",     "score": 7,  "pii_types": "aadhaar, ifsc",             "record_count": 198, "hours_ago": 72},
]

DEMO_FINDINGS = [
    ("aadhaar",  "XXXX-XXXX-3721", "pastebin",       "...Name: Rajesh Kumar, Aadhaar: XXXX-XXXX-3721, DOB: 12/04/1985..."),
    ("pan",      "ABXXX1234F",     "pastebin",       "...PAN: ABXXX1234F, Name: Priya Sharma, Income: 450000..."),
    ("mobile",   "981XXXX432",     "github_search",  "...mobile=9812344432, aadhaar=XXXX-XXXX-9821, state=Maharashtra..."),
    ("aadhaar",  "XXXX-XXXX-5512", "github_search",  "...aadhaar_no: XXXX-XXXX-5512, bank_acc: 9182XXXX1234..."),
    ("upi",      "raXXXX@gpay",    "pastebin",       "...upi_id: raXXXX@gpay, linked_mobile: 798XXXX321..."),
    ("ifsc",     "HDFC0XXXX34",    "controlc",       "...IFSC: HDFC0XXXX34, Acc: XXXX1234, Name: Amit Patel..."),
    ("pan",      "BCXXX9876G",     "controlc",       "...pan_card: BCXXX9876G, dob: 1990-07-23, gender: M..."),
    ("mobile",   "756XXXX890",     "paste_fo",       "...Contact: 7567898890, Aadhaar: XXXX-XXXX-4421, City: Chennai..."),
    ("aadhaar",  "XXXX-XXXX-8834", "github_search",  "...beneficiary_id: XXXX-XXXX-8834, scheme: PM-KISAN, amount: 6000..."),
    ("email_in", "suXXXX@gmail.in","pastebin",       "...email: suXXXX@gmail.in, phone: 901XXXX234, kyc: verified..."),
    ("aadhaar",  "XXXX-XXXX-2219", "github_search",  "...aadhaar: XXXX-XXXX-2219, pan: CDXXX4321H, upi: moXXXX@ybl..."),
    ("pan",      "CDXXX4321H",     "github_search",  "...pan: CDXXX4321H, aadhaar: XXXX-XXXX-2219, upi: moXXXX@ybl..."),
    ("upi",      "moXXXX@ybl",     "github_search",  "...upi: moXXXX@ybl, linked: 887XXXX123, balance_exposed: yes..."),
    ("ifsc",     "SBIN0XXXX91",    "paste_fo",       "...IFSC: SBIN0XXXX91, acc_no: XXXX7821, holder: Sunita Devi..."),
    ("mobile",   "623XXXX781",     "controlc",       "...ph: 6234567781, name: Vikram Singh, aadhaar: XXXX-XXXX-7712..."),
]

def ts(hours_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()

def seed():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # clear existing demo data
    cursor.execute("DELETE FROM incidents")
    cursor.execute("DELETE FROM findings")
    cursor.execute("DELETE FROM canaries")
    print("Cleared existing data.")

    # insert incidents
    for inc in DEMO_INCIDENTS:
        cursor.execute('''
            INSERT INTO incidents (source_url, source_type, severity, score, pii_types, record_count, alerted, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            inc["source_url"],
            inc["severity"],
            inc["score"],
            inc["pii_types"],
            inc["record_count"],
            1 if inc["severity"] in ("Critical", "High") else 0,
            ts(inc["hours_ago"])
        ))
    print(f"Inserted {len(DEMO_INCIDENTS)} incidents.")

    # insert findings
    for i, (match_type, masked, source_type, context) in enumerate(DEMO_FINDINGS):
        cursor.execute('''
    INSERT INTO incidents (source_url, severity, score, pii_types, record_count, alerted, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            DEMO_INCIDENTS[i % len(DEMO_INCIDENTS)]["source_url"],
            source_type,
            match_type,
            masked,
            context,
            ts(random.randint(1, 72))
        ))
    print(f"Inserted {len(DEMO_FINDINGS)} findings.")

    # insert canaries
    canaries = [
        ("2847 3901 5523", "CANRY1234C", "9001234567", "canary01@upi", "CANARY-001-AP-GOVT"),
        ("3712 8834 2201", "CANRY5678D", "8901234568", "canary02@ybl", "CANARY-002-MH-RATION"),
        ("5521 4409 8812", "CANRY9012E", "7801234569", "canary03@gpay","CANARY-003-TN-PENSION"),
    ]
    for fake_aadhaar, fake_pan, fake_phone, fake_upi, label in canaries:
        triggered = 1 if label == "CANARY-001-AP-GOVT" else 0
        cursor.execute('''
            INSERT INTO canaries (fake_aadhaar, fake_pan, fake_phone, fake_upi, label, planted_at, triggered)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (fake_aadhaar, fake_pan, fake_phone, fake_upi, label, ts(random.randint(24, 96)), triggered))
    print("Inserted 3 canaries (1 triggered).")

    conn.commit()
    conn.close()
    print("\nDemo data seeded successfully.")
    print("Run: python app.py — then open http://localhost:5000/api/stats")

if __name__ == "__main__":
    seed()
