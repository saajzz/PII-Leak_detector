"""
canary.py — Synthetic Data Poisoning Module
Generates fake but format-valid Indian PII records as tripwires.
If a canary appears in scraped content, it means a planted database was breached.
"""

import random
import string
import hashlib
import uuid
from datetime import datetime, timezone
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import get_connection

# ── VERHOEFF ALGORITHM (Aadhaar check digit) ────────────────────
VERHOEFF_TABLE_D = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0],
]
VERHOEFF_TABLE_P = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8],
]
VERHOEFF_TABLE_INV = [0,4,3,2,1,9,8,7,6,5]

def verhoeff_checksum(number_str):
    c = 0
    for i, digit in enumerate(reversed(number_str)):
        p = VERHOEFF_TABLE_P[(i+1) % 8][int(digit)]
        c = VERHOEFF_TABLE_D[c][p]
    return VERHOEFF_TABLE_INV[c]

def generate_fake_aadhaar():
    """Generate a format-valid Aadhaar with correct Verhoeff check digit."""
    # first digit must be 2-9
    first = random.randint(2, 9)
    middle = [random.randint(0, 9) for _ in range(10)]
    base = [first] + middle
    check = verhoeff_checksum("".join(map(str, base)))
    digits = base + [check]
    d = "".join(map(str, digits))
    return f"{d[:4]} {d[4:8]} {d[8:]}"

def generate_fake_pan():
    """Generate a format-valid PAN card number."""
    letters = string.ascii_uppercase
    # AAAAA9999A format
    part1 = "".join(random.choices(letters, k=5))
    part2 = "".join(random.choices(string.digits, k=4))
    part3 = random.choice(letters)
    return f"{part1}{part2}{part3}"

def generate_fake_phone():
    """Generate a format-valid Indian mobile number."""
    first = random.choice([6, 7, 8, 9])
    rest = "".join(random.choices(string.digits, k=9))
    return f"{first}{rest}"

def generate_fake_upi():
    """Generate a fake UPI ID."""
    providers = ["gpay", "paytm", "ybl", "okaxis", "oksbi", "ibl"]
    name_part = "".join(random.choices(string.ascii_lowercase, k=6))
    digits = "".join(random.choices(string.digits, k=3))
    return f"{name_part}{digits}@{random.choice(providers)}"

def generate_fake_ifsc():
    """Generate a format-valid IFSC code."""
    banks = ["HDFC", "SBIN", "ICIC", "AXIS", "PUNB", "UBIN", "CNRB"]
    bank = random.choice(banks)
    branch = "0" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{bank}{branch}"

# ── CANARY RECORD GENERATOR ──────────────────────────────────────
def generate_canary_record(label=None, context=None):
    """
    Generate a complete synthetic Indian PII record as a canary/tripwire.
    label   — identifies where this canary was planted (e.g. 'AP-GOVT-DB-2024')
    context — optional description of the target system
    """
    canary_id = str(uuid.uuid4())[:8].upper()

    if not label:
        label = f"CANARY-{canary_id}"

    record = {
        "canary_id":    canary_id,
        "label":        label,
        "context":      context or "Synthetic tripwire record",
        "fake_aadhaar": generate_fake_aadhaar(),
        "fake_pan":     generate_fake_pan(),
        "fake_phone":   generate_fake_phone(),
        "fake_upi":     generate_fake_upi(),
        "fake_ifsc":    generate_fake_ifsc(),
        "planted_at":   datetime.now(timezone.utc).isoformat(),
        "triggered":    0,
    }

    # generate a fingerprint hash for this canary
    fingerprint_raw = f"{record['fake_aadhaar']}{record['fake_pan']}{record['fake_phone']}"
    record["fingerprint"] = hashlib.sha256(fingerprint_raw.encode()).hexdigest()[:16]

    return record

def plant_canary(label=None, context=None):
    """Generate a canary record and save it to the database."""
    record = generate_canary_record(label, context)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO canaries (fake_aadhaar, fake_pan, fake_phone, fake_upi, label, planted_at, triggered)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        record["fake_aadhaar"],
        record["fake_pan"],
        record["fake_phone"],
        record["fake_upi"],
        record["label"],
        record["planted_at"],
        0
    ))
    conn.commit()
    conn.close()

    print(f"[CANARY PLANTED] {record['label']}")
    print(f"  Aadhaar : {record['fake_aadhaar']}")
    print(f"  PAN     : {record['fake_pan']}")
    print(f"  Phone   : {record['fake_phone']}")
    print(f"  UPI     : {record['fake_upi']}")
    print(f"  IFSC    : {record['fake_ifsc']}")
    print(f"  Hash    : {record['fingerprint']}")

    return record

def check_canaries_in_findings():
    """
    Cross-check all canary records against scraped findings.
    If a canary's Aadhaar/PAN/phone appears in findings → mark as triggered (breach detected).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM canaries WHERE triggered = 0")
    canaries = cursor.fetchall()

    triggered_count = 0

    for canary in canaries:
        # check if any finding's masked value matches canary patterns
        aadhaar_last4 = canary["fake_aadhaar"].replace(" ", "")[-4:]
        phone_last3   = canary["fake_phone"][-3:]

        cursor.execute('''
            SELECT COUNT(*) as cnt FROM findings
            WHERE masked_value LIKE ? OR masked_value LIKE ?
        ''', (f"%{aadhaar_last4}%", f"%{phone_last3}%"))

        result = cursor.fetchone()
        if result and result["cnt"] > 0:
            cursor.execute("UPDATE canaries SET triggered = 1 WHERE id = ?", (canary["id"],))
            print(f"[CANARY TRIGGERED] {canary['label']} — breach source identified!")
            triggered_count += 1

    conn.commit()
    conn.close()

    if triggered_count == 0:
        print("[CANARY CHECK] No canaries triggered.")
    else:
        print(f"[CANARY CHECK] {triggered_count} canary(ies) triggered — investigate immediately!")

    return triggered_count

def list_canaries():
    """Print all planted canaries and their status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canaries ORDER BY planted_at DESC")
    rows = cursor.fetchall()
    conn.close()

    print(f"\n{'─'*60}")
    print(f"  PLANTED CANARIES ({len(rows)} total)")
    print(f"{'─'*60}")
    for row in rows:
        status = "🔴 TRIGGERED" if row["triggered"] else "🟢 Safe"
        print(f"  [{status}] {row['label']}")
        print(f"    Aadhaar : {row['fake_aadhaar']}")
        print(f"    PAN     : {row['fake_pan']}")
        print(f"    Phone   : {row['fake_phone']}")
        print(f"    Planted : {row['planted_at']}")
        print()

# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("╔══════════════════════════════╗")
    print("║   CANARY MODULE — PII TRAP   ║")
    print("╚══════════════════════════════╝\n")

    # plant 3 demo canaries
    plant_canary(label="CANARY-001-AP-NREGA",    context="Andhra Pradesh NREGA database tripwire")
    print()
    plant_canary(label="CANARY-002-MH-RATION",   context="Maharashtra ration card database tripwire")
    print()
    plant_canary(label="CANARY-003-TN-PENSION",  context="Tamil Nadu pension portal tripwire")
    print()

    # check if any triggered
    check_canaries_in_findings()
    print()

    # list all
    list_canaries()
