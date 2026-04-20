import re
import os
from datetime import datetime, timezone

# ── COMPILED PATTERNS ──────────────────────────────────────────
PATTERNS = {
    # Allow both formatted (1234 5678 9012 / 1234-5678-9012) and compact (123456789012).
    "aadhaar": re.compile(r'(?<!\d)(?:[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4})(?!\d)'),
    "pan":     re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'),
    "mobile":  re.compile(r'\b[6-9][0-9]{9}\b'),
    "upi":     re.compile(r'[\w.\-]{2,256}@(oksbi|okaxis|ybl|ibl|axl|upi|paytm|gpay|phonepe|okicici)'),
    "ifsc":    re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
    "email_in":re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(in|co\.in)\b'),
}
DEBUG_PII = os.getenv("DEBUG_PII", "1") == "1"

# ── MASKING ─────────────────────────────────────────────────────
def mask_value(value, match_type):
    if match_type == "aadhaar":
        return "XXXX-XXXX-" + value.replace(" ", "")[-4:]
    elif match_type == "pan":
        return value[:2] + "XXX" + value[5:]
    elif match_type == "mobile":
        return value[:3] + "XXXX" + value[-3:]
    elif match_type == "upi":
        if "@" in value:
            parts = value.split("@")
            return parts[0][:2] + "XXXX@" + parts[1]
        return value[:4] + "XXXX"
    else:
        return value[:4] + "XXXX"

# ── MAIN SCAN FUNCTION ──────────────────────────────────────────
def scan_text(text, source_url="unknown", source_type="unknown"):
    findings = []

    for match_type, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if DEBUG_PII and match_type == "aadhaar":
            print(f"[DEBUG][aadhaar_matches] {source_url} -> {matches[:10]}")

        for match in matches:
            # get surrounding context (100 chars around match)
            start = text.find(match)
            context = text[max(0, start - 100): start + len(match) + 100]

            findings.append({
                "source_url":   source_url,
                "source_type":  source_type,
                "match_type":   match_type,
                "masked_value": mask_value(match, match_type),
                "context":      context.strip(),
                "detected_at":  datetime.now(timezone.utc).isoformat(),
                "raw_match":    match  # used for severity scoring, not stored
            })

    if DEBUG_PII:
        pii_types = sorted(set(f["match_type"] for f in findings))
        print(f"[DEBUG][detected_types] {source_url} -> {pii_types}")

    return findings

# ── TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_text = """
    User details leaked:
    Aadhaar: 2345 6789 0123
    PAN: ABCDE1234F
    Phone: 9876543210
    UPI: john.doe@gpay
    IFSC: HDFC0001234
    Email: user@example.in
    """

    results = scan_text(test_text, source_url="test", source_type="manual")

    for r in results:
        print(f"[{r['match_type'].upper()}] {r['masked_value']}")