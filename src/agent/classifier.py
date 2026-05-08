from datetime import date
from src.models import InvoiceRecord, EscalationStage

STAGE_MATRIX = {
    (1, 7): EscalationStage.STAGE_1,
    (8, 14): EscalationStage.STAGE_2,
    (15, 21): EscalationStage.STAGE_3,
    (22, 30): EscalationStage.STAGE_4,
}

def classify_record(record: InvoiceRecord) -> InvoiceRecord:
    """Compute days_overdue and assign escalation stage."""
    today = date.today()
    days_overdue = (today - record.due_date).days
    record.days_overdue = days_overdue
    
    if days_overdue <= 0:
        record.stage = EscalationStage.NOT_DUE
    elif days_overdue > 30:
        record.stage = EscalationStage.LEGAL
        record.is_escalated = True
    else:
        for (low, high), stage in STAGE_MATRIX.items():
            if low <= days_overdue <= high:
                record.stage = stage
                break
    
    return record

def get_tone(stage: EscalationStage) -> str:
    tone_map = {
        EscalationStage.STAGE_1: "warm_friendly",
        EscalationStage.STAGE_2: "polite_firm",
        EscalationStage.STAGE_3: "formal_serious",
        EscalationStage.STAGE_4: "stern_urgent",
        EscalationStage.LEGAL: "legal_flag",
    }
    return tone_map.get(stage, "warm_friendly")
