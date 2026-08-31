# ADR-015: Observability, Distributed Turn Spans & Prometheus Metrics

## Status
Accepted (v0.15.0)

## Context
Real-time Voice AI pipelines comprise multiple decoupled stages: audio ingestion, VAD endpointing, STT transcription, LLM Time-To-First-Token (TTFT), tool execution, TTS Time-To-First-Audio (TTFA), and barge-in cutoff. Without granular distributed tracing and metrics exposition, identifying bottlenecks across cloud providers is difficult. VoiceHire requires a dedicated telemetry engine to record turn spans and expose Prometheus-compatible metrics.

## Decision
1. **Turn Span Architecture**:
   - `TurnSpan` records start/end timestamps and latencies: `audio_ingest_ms`, `vad_endpoint_ms`, `stt_latency_ms`, `llm_ttft_ms`, `llm_total_ms`, `tool_execution_ms`, `tts_ttfa_ms`, `tts_total_ms`, `barge_in_latency_ms`, `e2e_latency_ms`.
   - Records provider identities and interruption status.

2. **Metrics Exporter & Prometheus Endpoint**:
   - `MetricsExporter` aggregates rolling statistics (total turns, total interruptions, average E2E latency, average TTFT, average TTFA).
   - Exposes `GET /metrics` in standard Prometheus text format.

## Consequences
### Positive
- Enables production monitoring with Prometheus / Grafana dashboards.
- Pinpoints latency bottlenecks across STT, LLM, and TTS providers.

### Tradeoffs
- Requires lightweight in-memory storage with rolling aggregation to avoid memory bloat.
