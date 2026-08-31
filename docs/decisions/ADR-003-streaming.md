# ADR-003: Realtime Streaming Pipeline & Clause-Boundary Chunking

## Status
Accepted (v0.3.0)

## Context
In conversational voice systems, waiting for the LLM to complete its entire response before beginning Text-to-Speech (TTS) synthesis introduces multi-second delays (1.5s - 3.5s+), making the conversation feel sluggish. To deliver human-like conversational responsiveness, synthesis must begin as early as possible without compromising acoustic naturalness.

## Decision
1. **Sentence / Clause Boundary Chunking**:
   - Implemented `SentenceBoundaryChunker` in `backend/app/voice/chunker.py`.
   - Streaming LLM tokens are buffered and emitted on punctuation boundaries (`.`, `!`, `?`, `;`, `\n`).
   - Each clause is concurrently streamed to TTS while the LLM continues generating subsequent clauses.

2. **Precision Telemetry for Latency Benchmarking**:
   - Created `StreamingMetricsTracker` to record:
     - `llm_ttft_ms`: Time to First Token.
     - `tts_ttfa_ms`: Time to First Audio chunk.
     - `total_perceived_ms`: Speech termination to first audible sound.

3. **Full-Duplex Streaming Transport**:
   - Exposed `WebSocket /api/voice/stream/ws` for bi-directional event, audio chunk, and token streaming.

## Consequences
### Positive
- Sub-second perceived response latency (< 800ms) with streaming cloud providers.
- TTS audio playback overlaps seamlessly with LLM generation.
- Full real-time visibility into per-turn latency bottlenecks.

### Tradeoffs
- Audio playback management requires client-side buffer queueing to avoid stutter between clause boundaries.
