import pytest
from app.security.sanitizer import PIISanitizer, SlidingWindowRateLimiter

def test_pii_sanitization():
    raw_text = "Hi, my email is rahul.sharma@example.com and phone is +1-555-234-5678. I also tested with key sk-abcdef1234567890abcdef1234567890."
    sanitized = PIISanitizer.sanitize(raw_text)
    
    assert "rahul.sharma@example.com" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "+1-555-234-5678" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "sk-abcdef1234567890" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized

def test_sliding_window_rate_limiter():
    SlidingWindowRateLimiter.reset()
    client = "client-ip-127.0.0.1"

    # Allow up to 3 requests in 10-second window
    for _ in range(3):
        assert SlidingWindowRateLimiter.is_allowed(client, max_requests=3, window_seconds=10.0) is True

    # 4th request must be rejected
    assert SlidingWindowRateLimiter.is_allowed(client, max_requests=3, window_seconds=10.0) is False
