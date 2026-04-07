import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.scraper import run_scraper
from modules.pattern_engine import scan_text
from modules.severity_score import score_findings
from database import get_connection, init_db
from datetime import datetime, timezone

def save_findings(findings):
    if not findings:
        return
    conn = get_connection()
    cursor = conn.cursor()
    for f in findings:
        cursor.execute('''
            INSERT INTO findings 
            (source_url, source_type, match_type, masked_value, context, detected_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            f["source_url"],
            f["source_type"],
            f["match_type"],
            f["masked_value"],
            f["context"],
            f["detected_at"]
        ))
    conn.commit()
    conn.close()

def save_incident(source_url, score_result, record_count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO incidents
        (source_url, severity, score, pii_types, record_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        source_url,
        score_result["severity"],
        score_result["score"],
        ", ".join(score_result["pii_types"]),
        record_count,
        datetime.now(timezone.utc).isoformat()
    ))
    conn.commit()
    conn.close()

def run_pipeline():
    print("\n══════════════════════════════")
    print("   PII LEAK DETECTOR RUNNING  ")
    print("══════════════════════════════\n")

    # Step 1 — scrape
    sources = run_scraper()

    total_findings = 0

    # Step 2 — scan each source
    for source in sources:
        findings = scan_text(
            source["content"],
            source_url=source["url"],
            source_type=source["source_type"]
        )

        if not findings:
            continue

        # Step 3 — score
        score_result = score_findings(findings)

        # Step 4 — save findings
        save_findings(findings)

        # Step 5 — save incident
        save_incident(source["url"], score_result, len(findings))

        total_findings += len(findings)

        print(f"[{score_result['severity'].upper()}] {source['url']}")
        print(f"  PII Types : {', '.join(score_result['pii_types'])}")
        print(f"  Score     : {score_result['score']}/10")
        print(f"  Findings  : {len(findings)}\n")

    print(f"══ Pipeline complete: {total_findings} total findings ══\n")

if __name__ == "__main__":
    init_db()
    run_pipeline()