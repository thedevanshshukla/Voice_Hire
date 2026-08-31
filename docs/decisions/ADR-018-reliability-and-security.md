# ADR-018: Reliability, PII Redaction & Sliding-Window Rate Limiting

## Status
Accepted (v0.18.0)

## Context
Production voice technical interview systems handle candidate speech containing private personal information (such as emails, phone numbers, and accidental API key disclosures). Additionally, public voice endpoints require rate limiting to prevent denial-of-service and unauthorized quota depletion.

## Decision
1. **PII Sanitizer**:
   - `PIISanitizer` executes regex-based redaction on candidate transcripts before persisting them to MongoDB Atlas and before feeding them into LLM prompt contexts.
   - Replaces detected emails with `[REDACTED_EMAIL]`, phone numbers with `[REDACTED_PHONE]`, and API keys with `[REDACTED_API_KEY]`.
2. **Sliding-Window Rate Limiting**:
   - `SlidingWindowRateLimiter` enforces request thresholds per client identity (default: 100 requests per 60 seconds) on critical endpoints (`/api/voice/token`, `/api/voice/turn`).

## Consequences
### Positive
- Protects candidate privacy and complies with data protection standards.
- Shields backend voice pipelines and downstream AI providers from spam.
