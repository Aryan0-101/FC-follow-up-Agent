import logging
from src.models import AgentState, AuditEntry, EscalationStage
from src.ingestion.csv_loader import load_invoices_from_csv
from src.agent.classifier import classify_record, get_tone
from src.llm.client import generate_email
from src.email_engine.sender import send_email
from src.audit.logger import log_audit_entry, log_event
from src.models import AgentState, AuditEntry, EscalationStage, WorkflowLog
from src.config import config

logger = logging.getLogger(__name__)

def ingest_node(state: AgentState) -> AgentState:
    """Load invoices if not already provided in state."""
    if not state.run_id:
        state.run_id = f"WF-{uuid.uuid4().hex[:8].upper()}"

    log_event(WorkflowLog(workflow_id=state.run_id, event_type="WORKFLOW_STARTED", status="SUCCESS"), "workflow")

    if not state.records:
        state.records = load_invoices_from_csv(config.CSV_PATH)
        log_event(WorkflowLog(workflow_id=state.run_id, event_type="INVOICES_LOADED", status="SUCCESS"), "workflow")
    return state

def classify_node(state: AgentState) -> AgentState:
    """Classify the current record."""
    if state.current_record:
        state.current_record = classify_record(state.current_record)
        log_event(WorkflowLog(
            workflow_id=state.run_id, 
            event_type="INVOICE_CLASSIFIED", 
            invoice_no=state.current_record.invoice_no,
            status="SUCCESS"
        ), "workflow")
    return state

def generate_email_node(state: AgentState) -> AgentState:
    """Generate email prose using LLM."""
    if state.current_record and state.current_record.stage != EscalationStage.LEGAL:
        try:
            state.generated_email = generate_email(state.current_record)
        except Exception as e:
            state.errors.append(f"Generation failed for {state.current_record.invoice_no}: {e}")
    return state

def send_email_node(state: AgentState) -> AgentState:
    """Dispatch the email."""
    if state.current_record and state.generated_email:
        success, status = send_email(state.current_record, state.generated_email)
        if success:
            state.total_sent += 1
        else:
            state.errors.append(f"Send failed for {state.current_record.invoice_no}: {status}")
    return state

def flag_legal_node(state: AgentState) -> AgentState:
    """Flag record for legal review (no email sent)."""
    if state.current_record:
        state.total_escalated += 1
        logger.info(f"FLAGGED FOR LEGAL: {state.current_record.invoice_no}")
    return state

def audit_node(state: AgentState) -> AgentState:
    """Create audit entry."""
    record = state.current_record
    email = state.generated_email
    
    if not record:
        return state

    # Mask email for privacy
    user, domain = record.client_email.split("@")
    masked_email = f"{user[0]}{'*'*(len(user)-1)}@{domain}"

    status = "skipped"
    if record.stage == EscalationStage.LEGAL:
        status = "escalated"
    elif email:
        status = "dry_run" if config.DRY_RUN else "sent"
    
    if state.errors:
        status = "failed"

    entry = AuditEntry(
        invoice_no=record.invoice_no,
        client_name=record.client_name,
        client_email_masked=masked_email,
        amount=record.amount,
        days_overdue=record.days_overdue or 0,
        stage=int(record.stage) if record.stage else None,
        tone=get_tone(record.stage) if record.stage else None,
        email_subject=email.subject if email else None,
        email_body_preview=email.body if email else None,
        send_status=status,
        error_message="; ".join(state.errors) if state.errors else None
    )
    
    log_audit_entry(entry)
    state.audit_entries.append(entry)
    return state

def update_follow_up_count_node(state: AgentState) -> AgentState:
    """Update internal counters (in a real app, this would write back to DB)."""
    if state.current_record:
        state.current_record.follow_up_count += 1
        state.total_processed += 1
    return state
