import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from src.config import config
from src.models import AuditEntry
import logging

logger = logging.getLogger(__name__)

engine = create_engine(f"sqlite:///{config.DB_PATH}")

def log_audit_entry(entry: AuditEntry) -> None:
    """Write audit entry to SQLite and JSON log."""
    _log_to_sqlite(entry)
    _log_to_json(entry)

def _log_to_sqlite(entry: AuditEntry) -> None:
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO audit_log 
            (invoice_no, client_name, client_email_masked, amount, days_overdue,
             stage, tone, email_subject, email_body_preview, send_status, 
             error_message, timestamp)
            VALUES (:invoice_no, :client_name, :client_email_masked, :amount,
                    :days_overdue, :stage, :tone, :email_subject, 
                    :email_body_preview, :send_status, :error_message, :timestamp)
        """), {
            "invoice_no": entry.invoice_no,
            "client_name": entry.client_name,
            "client_email_masked": entry.client_email_masked,
            "amount": entry.amount,
            "days_overdue": entry.days_overdue,
            "stage": entry.stage,
            "tone": entry.tone,
            "email_subject": entry.email_subject,
            "email_body_preview": entry.email_body_preview,
            "send_status": entry.send_status,
            "error_message": entry.error_message,
            "timestamp": entry.timestamp.isoformat()
        })
        conn.commit()

def _log_to_json(entry: AuditEntry) -> None:
    os.makedirs(os.path.dirname(config.AUDIT_JSON_PATH), exist_ok=True)
    
    existing = []
    if os.path.exists(config.AUDIT_JSON_PATH):
        with open(config.AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    
    existing.append(entry.model_dump(mode="json"))
    
    with open(config.AUDIT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, default=str)
