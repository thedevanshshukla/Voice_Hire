import re
import time
from typing import Dict, List, Tuple
from collections import defaultdict

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
API_KEY_REGEX = re.compile(r"(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})")

class PIISanitizer:
    """
    Sanitizes candidate transcripts before persistent storage and LLM context injection,
    redacting emails, phone numbers, and cloud API keys.
    """

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return ""

        sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        sanitized = API_KEY_REGEX.sub("[REDACTED_API_KEY]", sanitized)
        sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)
        return sanitized

class SlidingWindowRateLimiter:
    """
    In-memory sliding-window rate limiter preventing endpoint abuse and DDoS.
    """
    _requests: Dict[str, List[float]] = defaultdict(list)

    @classmethod
    def is_allowed(cls, client_key: str, max_requests: int = 60, window_seconds: float = 60.0) -> bool:
        now = time.time()
        window_start = now - window_seconds

        # Clean old timestamps
        cls._requests[client_key] = [t for t in cls._requests[client_key] if t > window_start]

        if len(cls._requests[client_key]) >= max_requests:
            return False

        cls._requests[client_key].append(now)
        return True

    @classmethod
    def reset(cls):
        cls._requests.clear()
