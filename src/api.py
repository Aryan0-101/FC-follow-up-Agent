from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json
from datetime import datetime

from src.config import config
from src.ingestion.csv_loader import load_invoices_from_csv
from src.agent.classifier import classify_record
from src.agent.graph import build_agent_graph
from src.models import AgentState, InvoiceRecord, EmailOutput
from src.audit.logger import LOG_PATHS
from src.utils.sanitiser import PROMPT_INJECTION_COUNT

from fastapi.responses import RedirectResponse
from src.scheduler.scheduler import start_scheduler

app = FastAPI(title="Finance AI API")

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class BatchRunResponse(BaseModel):
    workflow_id: str
    status: str

# --- Endpoints ---

@app.get("/invoices")
async def get_invoices():
    if not os.path.exists(config.CSV_PATH):
        return []
    records = load_invoices_from_csv(config.CSV_PATH)
    classified = [classify_record(r).model_dump() for r in records]
    return classified

@app.get("/stats")
async def get_stats():
    records = load_invoices_from_csv(config.CSV_PATH) if os.path.exists(config.CSV_PATH) else []
    classified = [classify_record(r) for r in records]
    
    overdue = [r for r in classified if r.days_overdue and r.days_overdue > 0]
    active = [r for r in classified if r.stage and 1 <= r.stage <= 4]
    legal = [r for r in classified if r.is_escalated]
    
    return {
        "total": len(classified),
        "overdue": len(overdue),
        "active": len(active),
        "legal": len(legal),
        "pending_recovery": sum(r.amount for r in overdue),
        "injection_attempts": PROMPT_INJECTION_COUNT
    }

@app.post("/generate-draft/{invoice_no}")
async def generate_draft(invoice_no: str):
    records = load_invoices_from_csv(config.CSV_PATH)
    record = next((r for r in records if r.invoice_no == invoice_no), None)
    if not record:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    from src.llm.client import generate_email
    record = classify_record(record)
    draft = generate_email(record)
    return draft

@app.post("/run-batch")
async def run_batch(background_tasks: BackgroundTasks):
    workflow_id = f"WF-{uuid.uuid4().hex[:6].upper()}"
    
    def process_batch():
        records = load_invoices_from_csv(config.CSV_PATH)
        graph = build_agent_graph()
        for r in records:
            if r.due_date <= datetime.now().date(): # Simple overdue check
                state = AgentState(records=[r], current_record=r, run_id=workflow_id)
                graph.invoke(state)

    background_tasks.add_task(process_batch)
    return {"workflow_id": workflow_id, "status": "started"}

@app.get("/logs/{category}")
async def get_logs(category: str):
    path = LOG_PATHS.get(category)
    if not path or not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

@app.get("/scheduler/status")
async def get_scheduler_status():
    from src.scheduler.scheduler import scheduler_instance
    if not scheduler_instance:
        return {"active": False, "next_run": None}
    
    jobs = scheduler_instance.get_jobs()
    if not jobs:
        return {"active": scheduler_instance.running, "next_run": None}
    
    next_run = jobs[0].next_run_time
    return {
        "active": scheduler_instance.running,
        "next_run": next_run.isoformat() if next_run else None,
        "server_time": datetime.now().isoformat()
    }

@app.post("/send-draft/{invoice_no}")
async def send_draft(invoice_no: str, draft: EmailOutput):
    records = load_invoices_from_csv(config.CSV_PATH)
    record = next((r for r in records if r.invoice_no == invoice_no), None)
    if not record:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    from src.email_engine.sender import send_email
    record = classify_record(record)
    success, status = send_email(record, draft)
    
    if success:
        # Manually trigger an audit log for this manual send
        from src.agent.nodes import AgentState
        from src.agent.graph import build_agent_graph
        # We invoke the graph with an 'already generated' email to just hit the audit/update nodes
        # But simpler is to just call the logger directly
        from src.audit.logger import log_audit_entry
        from src.models import AuditEntry
        
        user, domain = record.client_email.split("@")
        masked = f"{user[0]}{'*'*(len(user)-1)}@{domain}"
        
        log_audit_entry(AuditEntry(
            invoice_no=record.invoice_no,
            client_name=record.client_name,
            client_email_masked=masked,
            amount=record.amount,
            days_overdue=record.days_overdue or 0,
            stage=int(record.stage) if record.stage else None,
            tone=draft.tone_confirmed,
            email_subject=draft.subject,
            email_body_preview=draft.body,
            send_status="sent" if not config.DRY_RUN else "dry_run"
        ))
        
        return {"status": "success", "message": status}
    else:
        raise HTTPException(status_code=500, detail=status)

@app.post("/scheduler/{action}")
async def control_scheduler(action: str):
    # This would interact with the global scheduler instance
    # For now, we return success to the UI
    return {"status": "success", "action": action}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
