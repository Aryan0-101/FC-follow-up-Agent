from apscheduler.schedulers.background import BackgroundScheduler
from src.config import config
from src.agent.graph import build_agent_graph
from src.ingestion.csv_loader import load_invoices_from_csv
from src.models import AgentState
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global scheduler instance for API visibility
scheduler_instance = BackgroundScheduler()

def run_agent_job():
    logger.info("=== Finance Email Agent — Daily Run Started ===")
    records = load_invoices_from_csv(config.CSV_PATH)
    graph = build_agent_graph()
    
    for record in records:
        state = AgentState(records=[record], current_record=record, run_id=f"AUTO-{uuid.uuid4().hex[:6].upper()}")
        try:
            graph.invoke(state)
        except Exception as e:
            logger.error(f"Error processing {record.invoice_no}: {e}")
    
    logger.info("=== Daily Run Complete ===")

def start_scheduler():
    if not scheduler_instance.running:
        scheduler_instance.add_job(
            run_agent_job, 
            "cron", 
            hour=config.SCHEDULE_HOUR, 
            minute=config.SCHEDULE_MINUTE,
            id="daily_agent_run"
        )
        scheduler_instance.start()
        logger.info(f"Scheduler started — runs daily at {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}")

if __name__ == "__main__":
    start_scheduler()
    # Keep main thread alive
    import time
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler_instance.shutdown()
