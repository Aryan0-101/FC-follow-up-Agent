from apscheduler.schedulers.blocking import BlockingScheduler
from src.config import config
from src.agent.graph import build_agent_graph
from src.ingestion.csv_loader import load_invoices_from_csv
from src.models import AgentState
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_agent_job():
    logger.info("=== Finance Email Agent — Daily Run Started ===")
    
    records = load_invoices_from_csv(config.CSV_PATH)
    graph = build_agent_graph()
    
    for record in records:
        # Initialize state for each record
        state = AgentState(
            records=[record],
            current_record=record,
            run_id=str(uuid.uuid4())
        )
        try:
            final_state = graph.invoke(state)
            logger.info(
                f"Processed {record.invoice_no}: "
                f"status={final_state['audit_entries'][-1].send_status if final_state['audit_entries'] else 'N/A'}"
            )
        except Exception as e:
            logger.error(f"Error processing {record.invoice_no}: {e}")
    
    logger.info("=== Daily Run Complete ===")

def start_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_agent_job, 
        "cron", 
        hour=config.SCHEDULE_HOUR, 
        minute=config.SCHEDULE_MINUTE
    )
    logger.info(f"Scheduler started — runs daily at {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}")
    scheduler.start()

if __name__ == "__main__":
    # For testing, we can run the job immediately
    run_agent_job()
