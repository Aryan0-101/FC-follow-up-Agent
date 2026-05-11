import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from src.config import config
from src.models import AuditEntry, WorkflowLog, AILog, SecurityLog
from typing import Union
import logging

logger = logging.getLogger(__name__)

engine = create_engine(f"sqlite:///{config.DB_PATH}")

# Paths for different log categories
LOG_PATHS = {
    "audit": config.AUDIT_JSON_PATH,
    "workflow": "logs/workflow.json",
    "ai": "logs/ai_observability.json",
    "security": "logs/security.json"
}

def log_audit_entry(entry: AuditEntry) -> None:
    """Legacy wrapper for audit entries."""
    log_event(entry, "audit")
    _log_to_sqlite(entry)

def log_event(event: Union[AuditEntry, WorkflowLog, AILog, SecurityLog], category: str) -> None:
    """Write structured JSON log to the appropriate category file."""
    path = LOG_PATHS.get(category, "logs/misc.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    existing = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    
    existing.append(event.model_dump(mode="json"))
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, default=str)

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
