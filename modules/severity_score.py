# ── SEVERITY SCORING ────────────────────────────────────────────
# Each PII type has a base score
PII_SCORES = {
    "aadhaar":  6,
    "pan":      4,
    "mobile":   2,
    "upi":      3,
    "ifsc":     2,
    "email_in": 1,
}

# Score → Severity tier
def get_severity(score):
    if score >= 9:
        return "Critical"
    elif score >= 6:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"

# ── MAIN SCORING FUNCTION ───────────────────────────────────────
def score_findings(findings):
    if not findings:
        return {"severity": "Low", "score": 0, "pii_types": []}

    # get unique PII types found
    pii_types = list(set(f["match_type"] for f in findings))

    # add up scores
    total_score = sum(PII_SCORES.get(p, 1) for p in pii_types)

    # bulk dump bonus — if 50+ findings, add 2
    if len(findings) >= 50:
        total_score += 2

    # cap at 10
    total_score = min(total_score, 10)

    severity = get_severity(total_score)

    return {
        "severity":  severity,
        "score":     total_score,
        "pii_types": pii_types
    }

# ── TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    # simulate findings from pattern engine
    test_findings = [
        {"match_type": "aadhaar"},
        {"match_type": "pan"},
        {"match_type": "mobile"},
    ]

    result = score_findings(test_findings)
    print(f"PII Types : {result['pii_types']}")
    print(f"Score     : {result['score']}/10")
    print(f"Severity  : {result['severity']}")