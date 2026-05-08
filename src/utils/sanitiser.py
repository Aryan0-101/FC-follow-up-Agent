import re

INJECTION_PATTERNS = [
    r"(ignore|forget|disregard).{0,30}(above|previous|instruction)",
    r"(system|assistant|user)\s*:",
    r"<\|.+?\|>",             # Token injection attempts
    r"\[\[.+?\]\]",           # Bracket injection
]

def sanitise_field(value: str, max_len: int = 500) -> str:
    """Sanitise input fields to prevent prompt injection."""
    for pattern in INJECTION_PATTERNS:
        value = re.sub(pattern, "[REDACTED]", value, flags=re.IGNORECASE)
    return value.strip()[:max_len]
