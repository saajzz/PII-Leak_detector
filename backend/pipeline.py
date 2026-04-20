import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.scraper import run_scraper
from modules.pattern_engine import scan_text
from modules.severity_score import score_findings
from modules.alert_system import trigger_critical_alerts
from database import get_connection, init_db
from datetime import datetime, timezone
DEBUG_PII = os.getenv("DEBUG_PII", "1") == "1"


def _safe_console(text):
    return str(text).encode("ascii", "replace").decode("ascii")

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

def save_incident(source_url, source_type, score_result, record_count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO incidents
        (source_url, source_type, severity, score, pii_types, record_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        source_url,
        source_type,
        score_result["severity"],
        score_result["score"],
        ", ".join(score_result["pii_types"]),
        record_count,
        datetime.now(timezone.utc).isoformat()
    ))
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def run_pipeline():
    print("\n==============================")
    print("   PII LEAK DETECTOR RUNNING  ")
    print("==============================\n")

    # Step 1 — scrape
    sources = run_scraper()

    total_findings = 0

    # Step 2 — scan each source
    for source in sources:
        if DEBUG_PII:
            preview = _safe_console(source["content"][:300].replace("\n", "\\n"))
            print(f"[DEBUG][source_preview_300] {_safe_console(source['url'])} -> {preview}")
            print(f"[DEBUG][source_content_len] {_safe_console(source['url'])} -> {len(source['content'])}")

        findings = scan_text(
            source["content"],
            source_url=source["url"],
            source_type=source["source_type"]
        )

        if not findings:
            continue

        # Step 3 — score
        if DEBUG_PII:
            detected_types = sorted(set(f["match_type"] for f in findings))
            print(f"[DEBUG][before_scoring_types] {_safe_console(source['url'])} -> {detected_types}")
        score_result = score_findings(findings)

        # Step 4 — save findings
        save_findings(findings)

        # Step 5 — save incident
        incident_id = save_incident(
            source["url"],
            source["source_type"],
            score_result,
            len(findings),
        )
        trigger_critical_alerts(
            {
                "id": incident_id,
                "source_url": source["url"],
                "severity": score_result["severity"],
                "score": score_result["score"],
                "pii_types": ", ".join(score_result["pii_types"]),
                "record_count": len(findings),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        total_findings += len(findings)

        print(f"[{score_result['severity'].upper()}] {source['url']}")
        print(f"  PII Types : {', '.join(score_result['pii_types'])}")
        print(f"  Score     : {score_result['score']}/10")
        print(f"  Findings  : {len(findings)}\n")

    print(f"== Pipeline complete: {total_findings} total findings ==\n")

if __name__ == "__main__":
    init_db()
    run_pipeline()