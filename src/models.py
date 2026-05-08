from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional, Literal
from enum import IntEnum

class EscalationStage(IntEnum):
    NOT_DUE = 0
    STAGE_1 = 1   # 1-7 days overdue
    STAGE_2 = 2   # 8-14 days overdue
    STAGE_3 = 3   # 15-21 days overdue
    STAGE_4 = 4   # 22-30 days overdue
    LEGAL = 5     # 30+ days overdue

ToneType = Literal["warm_friendly", "polite_firm", "formal_serious", "stern_urgent", "legal_flag"]

class InvoiceRecord(BaseModel):
    invoice_no: str
    client_name: str
    client_email: str
    amount: float
    currency: str = "INR"
    due_date: date
    follow_up_count: int = 0
    contact_person: str
    payment_link: str
    days_overdue: Optional[int] = None
    stage: Optional[EscalationStage] = None
    is_escalated: bool = False

class EmailOutput(BaseModel):
    subject: str = Field(..., max_length=150, description="Email subject line")
    body: str = Field(..., min_length=50, max_length=1500, description="Email body text")
    tone_confirmed: ToneType
    cta: str = Field(..., description="Call to action text")

class AuditEntry(BaseModel):
    invoice_no: str
    client_name: str
    client_email_masked: str
    amount: float
    days_overdue: int
    stage: Optional[int]
    tone: Optional[str]
    email_subject: Optional[str]
    email_body_preview: Optional[str]
    send_status: Literal["sent", "dry_run", "failed", "escalated", "skipped"]
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentState(BaseModel):
    """LangGraph state passed between nodes."""
    records: list[InvoiceRecord] = []
    current_record: Optional[InvoiceRecord] = None
    generated_email: Optional[EmailOutput] = None
    audit_entries: list[AuditEntry] = []
    errors: list[str] = []
    run_id: str = ""
    total_processed: int = 0
    total_sent: int = 0
    total_escalated: int = 0
    total_skipped: int = 0
