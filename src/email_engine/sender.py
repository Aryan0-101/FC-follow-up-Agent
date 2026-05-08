import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from src.config import config
from src.models import InvoiceRecord, EmailOutput
import logging

logger = logging.getLogger(__name__)

def send_email(record: InvoiceRecord, email: EmailOutput) -> tuple[bool, str]:
    """Send email or dry-run log. Returns (success, status_message)."""
    
    if config.DRY_RUN:
        return _dry_run_save(record, email)
    else:
        return _smtp_send(record, email)

def _dry_run_save(record: InvoiceRecord, email: EmailOutput) -> tuple[bool, str]:
    os.makedirs(config.DRY_RUN_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{config.DRY_RUN_DIR}{record.invoice_no}_{timestamp}.txt"
    
    content = f"""
=== DRY RUN EMAIL ===
TO: {record.client_email}
FROM: {config.SENDER_NAME} <{config.SENDER_EMAIL}>
SUBJECT: {email.subject}
TONE: {email.tone_confirmed}
TIMESTAMP: {timestamp}
========================

{email.body}

---
CTA: {email.cta}
Payment Link: {record.payment_link}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"[DRY RUN] Email saved: {filename}")
    return True, "dry_run"

def _smtp_send(record: InvoiceRecord, email: EmailOutput) -> tuple[bool, str]:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = email.subject
        msg["From"] = f"{config.SENDER_NAME} <{config.SENDER_EMAIL}>"
        msg["To"] = record.client_email
        
        body_text = f"{email.body}\n\n{email.cta}\nPayment Link: {record.payment_link}"
        msg.attach(MIMEText(body_text, "plain"))
        
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent to {record.client_email} for {record.invoice_no}")
        return True, "sent"
        
    except Exception as e:
        logger.error(f"SMTP failed for {record.invoice_no}: {e}")
        return False, f"failed: {str(e)}"
