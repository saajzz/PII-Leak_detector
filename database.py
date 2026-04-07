import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pii_detector.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            url TEXT NOT NULL,
            last_fetched TEXT,
            fetch_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            source_type TEXT,
            match_type TEXT,
            masked_value TEXT,
            context TEXT,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            severity TEXT,
            score INTEGER,
            pii_types TEXT,
            record_count INTEGER DEFAULT 1,
            alerted INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS canaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fake_aadhaar TEXT,
            fake_pan TEXT,
            fake_phone TEXT,
            fake_upi TEXT,
            label TEXT,
            planted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            triggered INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            channel TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            delivery_status TEXT
        );
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()