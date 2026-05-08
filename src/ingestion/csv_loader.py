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
                contact_person=sanitise_field(str(row.get("contact_person", row["client_name"]))),
                payment_link=str(row.get("payment_link", "#")),
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Skipping invalid row {row.get('invoice_no', '?')}: {e}")
    
    logger.info(f"Loaded {len(records)} invoice records from {path}")
    return records
