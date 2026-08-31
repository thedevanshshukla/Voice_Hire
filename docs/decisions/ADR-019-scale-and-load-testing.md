# ADR-019: Multi-Room Concurrent Load Simulation & Latency Distribution

## Status
Accepted (v0.19.0)

## Context
Voice AI systems experience non-linear latency degradation under high concurrent room volume. To certify VoiceHire for high-volume enterprise hiring rounds, we require a built-in synthetic load testing harness measuring throughput and latency percentiles (P50, P95, P99).

## Decision
1. **Concurrent Load Simulator**:
   - `ConcurrentLoadSimulator` executes parallel asynchronous interview sessions against the voice pipeline.
   - Measures turn latencies across workers and computes throughput (turns/second) alongside P50, P95, and P99 latency percentiles.
2. **REST Endpoints**:
   - `POST /api/scale/run-load-test`
   - `GET /api/scale/load-test-results`

## Consequences
### Positive
- Validates system stability under multi-candidate concurrent loads.
- Provides immediate empirical benchmarking for infrastructure sizing.
