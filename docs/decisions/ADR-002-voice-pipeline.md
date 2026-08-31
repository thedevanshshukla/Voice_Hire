# ADR-002: Modular Voice Provider Abstractions & LiveKit Pipeline

## Status
Accepted (v0.2.0)

## Context
VoiceHire requires real-time conversational capabilities combining Speech-to-Text (STT), Large Language Models (LLM), and Text-to-Speech (TTS). To avoid tight coupling to any single vendor and to support local deterministic testing, development simulation, and multi-cloud experimentation, the core pipeline needed a modular abstraction layer.

## Decision
1. **Provider Abstraction Pattern**:
   - Defined `BaseSTTProvider`, `BaseLLMProvider`, and `BaseTTSProvider` abstract interfaces.
   - Built pluggable implementations for Deepgram, OpenAI, Gemini, ElevenLabs, alongside lightweight `Mock*` providers for zero-dependency local development and testing.
   - Implemented `VoiceProviderFactory` for dynamic provider resolution driven by environment configuration (`.env`).

2. **Latency Tracking & Diagnostics**:
   - Integrated per-stage latency metrics (`stt_latency_ms`, `llm_latency_ms`, `tts_latency_ms`, `total_latency_ms`) directly into turn execution results.

3. **LiveKit Integration**:
   - Implemented JWT token generation with `VideoGrants` in `backend/app/agent/worker.py` and exposed via `POST /api/voice/token`.
   - Structured the worker to support future WebRTC streaming sessions.

## Consequences
### Positive
- Zero external API dependency required to run unit tests and local frontend simulations.
- Seamless provider swapping for benchmarking and experimentation without touching interview state logic.
- Real-time latency visibility on every conversational turn.

### Tradeoffs
- Additional boilerplate abstraction layer across providers.
