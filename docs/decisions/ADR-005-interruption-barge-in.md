# ADR-005: Real-time Barge-In & Audio Track Cancellation

## Status
Accepted (v0.5.0)

## Context
In natural technical interviews, candidates frequently interrupt the interviewer to clarify a requirement, correct an assumption, or provide a faster answer. Traditional voice bots that ignore user speech while speaking feel rigid and robotic. A production Voice AI system must support instant barge-in by cancelling active speech synthesis and token generation with sub-200ms latency.

## Decision
1. **Asynchronous Cancellation Token Pattern**:
   - Implemented `CancellationToken` in `backend/app/voice/interruption/cancellation.py`.
   - Propagated through all async generator loops (LLM token generation and TTS audio synthesis).
   - Allows instant cooperative termination without leaking background tasks or orphaned audio frames.

2. **Barge-In Detector**:
   - Implemented `BargeInDetector` in `backend/app/voice/interruption/barge_in.py`.
   - Actively monitors candidate audio frames whenever `is_agent_speaking=True` or `is_agent_generating=True`.
   - When candidate speech is sustained for ≥ 120ms (filtering acoustic echo and short noises), immediately triggers cancellation token.

3. **Client-Side Audio Buffer Teardown**:
   - Upon receiving `interrupted` event over WebSocket or detecting user speech locally, the client immediately mutes and clears active Web Audio / HTML5 audio elements.

4. **Telemetry & Benchmarking**:
   - Measuring `interruption_detection_ms` and `cancellation_latency_ms` to ensure total barge-in cutoff latency remains under 200ms.

## Consequences
### Positive
- Candidate experiences natural conversational freedom to interrupt and redirect the conversation.
- Fast cancellation (< 200ms) preserves conversational tempo and avoids awkward overlapping audio.
- Prevents token and TTS API credit waste on truncated agent responses.

### Tradeoffs
- Requires acoustic echo cancellation (AEC) in hardware/browser to prevent the agent's own speaker output from falsely triggering barge-in.
