import json
import logging
import time
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from src.config import config
from src.models import EmailOutput, InvoiceRecord, AILog
from src.llm.prompts import SYSTEM_PROMPT, STAGE_PROMPTS
from src.agent.classifier import get_tone
from src.audit.logger import log_event

# Enable SQLite caching for dev
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

logger = logging.getLogger(__name__)

# Initialize NVIDIA NIM client
llm = ChatNVIDIA(
    model=config.LLM_MODEL,
    nvidia_api_key=config.NVIDIA_API_KEY,
    max_tokens=config.LLM_MAX_TOKENS,
    temperature=config.LLM_TEMPERATURE,
)

def generate_email(record: InvoiceRecord) -> EmailOutput:
    """Generate a personalised email for the given invoice record using NVIDIA NIM."""
    start_time = time.time()
    tone = get_tone(record.stage)
    prompt_template = STAGE_PROMPTS.get(tone)
    
    if not prompt_template:
        raise ValueError(f"No prompt template found for tone: {tone}")

    user_prompt = prompt_template.format(
        invoice_no=record.invoice_no,
        client_name=record.client_name,
        contact_person=record.contact_person,
        currency=record.currency,
        amount=record.amount,
        due_date=record.due_date.strftime("%d %b %Y"),
        days_overdue=record.days_overdue,
        payment_link=record.payment_link,
        follow_up_count=record.follow_up_count,
    )
    
    for attempt in range(2):  # Retry once on validation failure
        try:
            # NVIDIA NIM via LangChain
            messages = [
                ("system", SYSTEM_PROMPT),
                ("user", user_prompt),
            ]
            response = llm.invoke(messages)
            latency = int((time.time() - start_time) * 1000)
            
            raw_json = response.content.strip()
            # Strip any accidental markdown fences
            raw_json = raw_json.replace("```json", "").replace("```", "").strip()
            
            # Robust JSON extraction
            try:
                # Try direct parse first
                data = json.loads(raw_json)
            except json.JSONDecodeError:
                # If direct parse fails, try finding the first { and last }
                if "{" in raw_json and "}" in raw_json:
                    start_index = raw_json.find("{")
                    end_index = raw_json.rfind("}") + 1
                    raw_json = raw_json[start_index:end_index]
                    data = json.loads(raw_json)
                else:
                    raise
            
            email_output = EmailOutput(**data)
            
            # Log AI success
            log_event(AILog(
                workflow_id=getattr(record, 'workflow_id', 'MANUAL-DRAFT'),
                invoice_no=record.invoice_no,
                model=config.LLM_MODEL,
                latency_ms=latency,
                validation="PASSED"
            ), "ai")
            
            return email_output
            
        except Exception as e:
            logger.warning(f"LLM attempt {attempt+1} failed for {record.invoice_no}: {e}")
            if attempt == 1:
                # Return a basic fallback if LLM fails repeatedly
                return EmailOutput(
                    subject=f"URGENT: Payment Reminder for Invoice {record.invoice_no}",
                    body=f"Dear {record.contact_person},\n\nThis is a reminder regarding your overdue invoice {record.invoice_no} for {record.currency} {record.amount:,.2f}. Please arrange payment as soon as possible.\n\nThank you.",
                    tone_confirmed="polite_firm",
                    cta="Please pay via the link below."
                )
    return None
