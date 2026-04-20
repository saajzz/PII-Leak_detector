import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

from database import get_connection

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_PATH)


def _log_alert(incident_id, channel, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO alerts_log (incident_id, channel, sent_at, delivery_status)
        VALUES (?, ?, ?, ?)
        """,
        (incident_id, channel, datetime.now(timezone.utc).isoformat(), status),
    )
    conn.commit()
    conn.close()


def _build_message(incident):
    return (
        f"Critical PII leak detected\n\n"
        f"Incident ID: {incident['id']}\n"
        f"Source: {incident['source_url']}\n"
        f"Severity: {incident['severity']}\n"
        f"Score: {incident['score']}/10\n"
        f"PII Types: {incident['pii_types']}\n"
        f"Record Count: {incident['record_count']}\n"
        f"Detected At: {incident['created_at']}\n"
    )


def send_email_alert(incident):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    alert_from = os.getenv("ALERT_FROM_EMAIL", smtp_user or "")
    alert_to = os.getenv("ALERT_TO_EMAIL")

    if not all([smtp_host, smtp_user, smtp_password, alert_to]):
        return False, "missing_email_config"

    subject = f"[CRITICAL] PII Leak #{incident['id']}"
    body = _build_message(incident)
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = alert_from
    msg["To"] = alert_to

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(alert_from, [alert_to], msg.as_string())
        return True, "sent"
    except Exception as e:
        return False, f"error:{e}"


def send_sms_alert(incident):
    # Twilio-based SMS via REST API.
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE")
    to_phone = os.getenv("ALERT_TO_PHONE")

    if not all([account_sid, auth_token, from_phone, to_phone]):
        return False, "missing_sms_config"

    body = (
        f"CRITICAL PII leak #{incident['id']} | "
        f"score={incident['score']} | "
        f"types={incident['pii_types']} | "
        f"url={incident['source_url']}"
    )
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    try:
        resp = requests.post(
            endpoint,
            data={"From": from_phone, "To": to_phone, "Body": body[:1600]},
            auth=(account_sid, auth_token),
            timeout=15,
        )
        if 200 <= resp.status_code < 300:
            return True, "sent"
        return False, f"http_{resp.status_code}"
    except Exception as e:
        return False, f"error:{e}"


def trigger_critical_alerts(incident):
    if incident.get("severity") != "Critical":
        return

    email_ok, email_status = send_email_alert(incident)
    _log_alert(incident["id"], "email", email_status if email_ok else email_status)

    sms_ok, sms_status = send_sms_alert(incident)
    _log_alert(incident["id"], "sms", sms_status if sms_ok else sms_status)

    if email_ok or sms_ok:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE incidents SET alerted = 1 WHERE id = ?", (incident["id"],))
        conn.commit()
        conn.close()
