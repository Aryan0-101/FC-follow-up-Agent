import pandas as pd
from datetime import date
from src.models import InvoiceRecord
from src.utils.sanitiser import sanitise_field
import logging

logger = logging.getLogger(__name__)

def load_invoices_from_csv(path: str) -> list[InvoiceRecord]:
    """Load and validate invoice records from CSV."""
    df = pd.read_csv(path, parse_dates=["due_date"])
    df.columns = df.columns.str.strip().str.lower()
    
    records = []
    for _, row in df.iterrows():
        try:
            record = InvoiceRecord(
                invoice_no=sanitise_field(str(row["invoice_no"])),
                client_name=sanitise_field(str(row["client_name"])),
                client_email=str(row["client_email"]).strip(),
                amount=float(row["amount"]),
                currency=str(row.get("currency", "INR")),
                due_date=row["due_date"].date(),
                follow_up_count=int(row.get("follow_up_count", 0)),
                last_follow_up_date=pd.to_datetime(row["last_follow_up_date"]).date() if pd.notna(row.get("last_follow_up_date")) else None,
                last_notified_stage=int(row.get("last_notified_stage", 0)),
                contact_person=sanitise_field(str(row.get("contact_person", row["client_name"]))),
                payment_link=str(row.get("payment_link", "#")),
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Skipping invalid row {row.get('invoice_no', '?')}: {e}")
    
    logger.info(f"Loaded {len(records)} invoice records from {path}")
    return records

def update_invoice_in_csv(path: str, invoice_no: str, follow_up_count: int, last_date: date, last_notified_stage: int):
    """Update a specific invoice record in the CSV file."""
    try:
        df = pd.read_csv(path)
        # Ensure column names match what we expect
        df.columns = df.columns.str.strip().str.lower()
        
        # Check if columns exist, if not add them
        if "last_follow_up_date" not in df.columns:
            df["last_follow_up_date"] = None
        if "last_notified_stage" not in df.columns:
            df["last_notified_stage"] = 0

        idx = df[df["invoice_no"] == invoice_no].index
        if not idx.empty:
            df.loc[idx, "follow_up_count"] = follow_up_count
            df.loc[idx, "last_follow_up_date"] = last_date.isoformat()
            df.loc[idx, "last_notified_stage"] = last_notified_stage
            df.to_csv(path, index=False)
            logger.info(f"Persisted follow-up update for {invoice_no}")
    except Exception as e:
        logger.error(f"Failed to update CSV for {invoice_no}: {e}")
