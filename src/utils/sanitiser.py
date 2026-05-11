import re

# Simple global counter for security stats
PROMPT_INJECTION_COUNT = 0

INJECTION_PATTERNS = [
    r"(ignore|forget|disregard).{0,30}(above|previous|instruction)",
    r"(system|assistant|user)\s*:",
    r"<\|.+?\|>",             # Token injection attempts
    r"\[\[.+?\]\]",           # Bracket injection
]

def sanitise_field(value: str, max_len: int = 500) -> str:
    """Sanitise input fields to prevent prompt injection."""
    global PROMPT_INJECTION_COUNT
    original = value
    for pattern in INJECTION_PATTERNS:
        value = re.sub(pattern, "[REDACTED]", value, flags=re.IGNORECASE)
    
    if "[REDACTED]" in value:
        PROMPT_INJECTION_COUNT += 1
        from src.audit.logger import log_event
        from src.models import SecurityLog
        log_event(SecurityLog(
            event_type="PROMPT_INJECTION_BLOCKED",
            detected_text=original[:100],
            risk_level="HIGH"
        ), "security")
        
    return value.strip()[:max_len]
