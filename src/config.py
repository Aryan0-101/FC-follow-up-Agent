import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "meta/llama-3.1-405b-instruct")
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.3  # Low temp for consistent professional tone
    
    # Email
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "finance@yourcompany.com")
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Finance Team")
    
    # Data
    CSV_PATH: str = os.getenv("CSV_PATH", "data/invoices_mock.csv")
    DB_PATH: str = os.getenv("DB_PATH", "data/finance_agent.db")
    
    # Audit
    AUDIT_JSON_PATH: str = "logs/audit.json"
    DRY_RUN_DIR: str = "logs/dry_run/"
    
    # Scheduling
    SCHEDULE_HOUR: int = int(os.getenv("SCHEDULE_HOUR", "9"))
    SCHEDULE_MINUTE: int = int(os.getenv("SCHEDULE_MINUTE", "0"))
    
    # Security
    MAX_EMAILS_PER_RUN: int = int(os.getenv("MAX_EMAILS_PER_RUN", "200"))
    
    # Observability
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "finance-email-agent")

config = Config()
