from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db, get_connection
from pipeline import run_pipeline
import threading

app = Flask(__name__)
CORS(app)

# ── ROUTES ──────────────────────────────────────────────────────

@app.route("/")
def home():
    return jsonify({"status": "PII Leak Detector API is running"})

@app.route("/api/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM incidents")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as critical FROM incidents WHERE severity = 'Critical'")
    critical = cursor.fetchone()["critical"]

    cursor.execute("SELECT COUNT(*) as high FROM incidents WHERE severity = 'High'")
    high = cursor.fetchone()["high"]

    cursor.execute("SELECT COUNT(*) as total FROM findings")
    total_findings = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as triggered FROM canaries WHERE triggered = 1")
    triggered_canaries = cursor.fetchone()["triggered"]

    conn.close()

    return jsonify({
        "total_incidents":    total,
        "critical_incidents": critical,
        "high_incidents":     high,
        "total_findings":     total_findings,
        "triggered_canaries": triggered_canaries
    })

@app.route("/api/incidents")
def get_incidents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM incidents
        ORDER BY created_at DESC
        LIMIT 100
    ''')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/findings")
def get_findings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM findings
        ORDER BY detected_at DESC
        LIMIT 100
    ''')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/sources")
def get_sources():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source_type, COUNT(*) as count
        FROM incidents
        GROUP BY source_type
    ''')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/severity-breakdown")
def get_severity_breakdown():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT severity, COUNT(*) as count
        FROM incidents
        GROUP BY severity
    ''')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/canaries")
def get_canaries():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canaries ORDER BY planted_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/api/run-pipeline", methods=["POST"])
def trigger_pipeline():
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "Pipeline started"})

# ── START ────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)