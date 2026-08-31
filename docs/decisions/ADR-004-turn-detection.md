# ADR-004: Voice Activity Detection (VAD) & Natural Turn Taking

## Status
Accepted (v0.4.0)

## Context
In live technical interviews, candidates frequently pause for 300ms–600ms mid-sentence to think, breathe, or structure complex technical ideas. Naive voice systems that terminate candidate turns upon any detected silence cut off candidates prematurely. Conversely, waiting too long (e.g. > 2.5s) causes uncomfortable conversational delays.

## Decision
1. **Energy / RMS Voice Activity Detector with Adaptive Noise Floor**:
   - Implemented `EnergyVADProvider` in `backend/app/voice/vad/providers/energy.py`.
   - Utilizes an Exponential Moving Average (EMA) noise floor model to dynamically adjust speech energy thresholds against background room acoustic conditions.

2. **Intelligent State Machine Endpointing**:
   - Implemented `TurnDetector` in `backend/app/voice/vad/turn_detector.py`.
   - States: `IDLE -> CANDIDATE_SPEAKING -> CANDIDATE_PAUSED -> TURN_ENDPOINT`.
   - Short pauses (< 600ms) transition into `CANDIDATE_PAUSED` where the agent waits naturally and increments `pause_count`.
   - Terminal silences (≥ 800ms) after qualifying speech duration (≥ 250ms) trigger clean `TURN_ENDPOINT` execution.
   - Spurious microphone clicks (< 250ms) are filtered out without triggering false AI responses.

3. **Configurable Endpointing Thresholds**:
   - Exposing `silence_threshold_ms` via `.env` (`VAD_SILENCE_THRESHOLD_MS`) and frontend slider (400ms - 1600ms).

## Consequences
### Positive
- Prevents premature interruptions during natural candidate thinking pauses.
- Dynamic noise floor tracking works across varied microphones and room acoustics without requiring native OS drivers.
- Full turn telemetry tracking active speech duration, intra-turn pause counts, and endpointing delay.

### Tradeoffs
- Pure energy VAD requires careful threshold calibration in high-noise environments compared to heavier deep-learning VAD models (e.g., Silero).
