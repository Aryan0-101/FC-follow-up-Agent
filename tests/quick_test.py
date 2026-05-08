from src.ingestion.csv_loader import load_invoices_from_csv
from src.agent.classifier import classify_record
from src.config import config
import os

def test_pipeline():
    print("Testing Ingestion...")
    if not os.path.exists(config.CSV_PATH):
        print(f"Error: {config.CSV_PATH} not found.")
        return

    records = load_invoices_from_csv(config.CSV_PATH)
    print(f"Loaded {len(records)} records.")

    print("\nTesting Classification...")
    for record in records:
        classified = classify_record(record)
        print(f"Invoice: {classified.invoice_no} | Due: {classified.due_date} | Days Overdue: {classified.days_overdue} | Stage: {classified.stage.name if classified.stage else 'None'}")

if __name__ == "__main__":
    test_pipeline()
