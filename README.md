# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct structured, adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, an adaptive question engine with depth probing, evidence-based evaluations, mid-interview Knowledge Base RAG, conversational memory, agent tool execution, multilingual English + Hindi + Hinglish support, distributed observability metrics, A/B experimentation, and automated evaluation benchmark suites.

---

## 🗺️ Version Progression

- [x] **`v0.1.0` (Project Foundation)**
- [x] **`v0.2.0` (Basic Voice Pipeline)**
- [x] **`v0.3.0` (Realtime / Streaming)**
- [x] **`v0.4.0` (Natural Turn Taking)**
- [x] **`v0.5.0` (Interruption & Barge-In)**
- [x] **`v0.6.0` (Interview Foundation)**
- [x] **`v0.7.0` (Interview State Machine)**
- [x] **`v0.8.0` (Adaptive Question Engine)**
- [x] **`v0.9.0` (Answer Evaluation Engine)**
- [x] **`v0.10.0` (Evidence-Based Evaluation)**
- [x] **`v0.11.0` (Knowledge Base & RAG)**
- [x] **`v0.12.0` (Memory & Cross-Turn Synthesis)**
- [x] **`v0.13.0` (Agent Tools / Actions)**
- [x] **`v0.14.0` (Multilingual support: English + Hindi + Hinglish)**
- [x] **`v0.15.0` (Observability & Prometheus Telemetry)**
- [x] **`v0.16.0` (Voice AI Experimentation & A/B Testing)**
- [x] **`v0.17.0` (Evaluation Suite & Benchmark Runner)** ── *Current Release*
- [ ] `v0.18.0` (Reliability & Security)
- [ ] `v0.19.0` (Scale & Load Testing)
- [ ] `v1.0.0` (Final Production Polish)

---

## 🏗️ Architecture (v0.17.0)

```
                    ┌──────────────────────────────┐
                    │      Candidate Browser       │
                    │   React / Vite / TypeScript  │
                    │  - Latency Waterfall HUD     │
                    │  - A/B Experiment Badge (🧪) │
                    │  - Evaluation Benchmark Tab  │
                    │  - Language Selector & HUD   │
                    │  - Architecture Diagram View │
                    │  - Python Sandbox Console    │
                    └──────────────┬───────────────┘
                                   │
                      WebSocket / REST / WebRTC
                                   │
                    ┌──────────────▼───────────────┐
                    │       FastAPI Backend        │
                    │  - GET /metrics (Prometheus) │
                    │  - /api/experiments/*        │
                    │  - /api/evaluation/*         │
                    │  - /api/agent/tools          │
                    │  - WS /api/voice/stream/ws   │
                    └──────────────┬───────────────┘
                                   │
     ┌──────────────────────┬──────┴───────────────┬──────────────────────┐
     ▼                      ▼                      ▼                      ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ Observability│       │ A/B Engine  │        │ Benchmark   │        │ Agent Tools │
│ (TurnSpan & │        │ (Variant    │        │ Runner      │        │ & Memory    │
│ Prometheus) │        │ Allocation) │        │ (MAE Eval)  │        │ Engines     │
└─────────────┘        └─────────────┘        └─────────────┘        └─────────────┘
```

---

## ✨ Key Capabilities

- **Evaluation Benchmark Suite & Scoring Calibration (`v0.17.0`)**: Pre-packaged golden candidate transcripts across SDE-1, SDE-2, Senior, and Staff levels automatically calibrated against human grading baselines, computing Mean Absolute Error (MAE < 1.0) and red flag precision/recall.
- **Voice AI A/B Experimentation (`v0.16.0`)**: Online multi-variant A/B testing comparing LLMs (Gemini 1.5 Flash vs OpenAI GPT-4o-mini), TTS engines (Deepgram Aura vs ElevenLabs Multilingual), and chunking strategies on live turn latencies and scorecard scores.
- **Distributed Observability & Prometheus Telemetry (`v0.15.0`)**: Granular `TurnSpan` tracking across audio ingestion, VAD endpointing, STT, LLM TTFT, tool execution, and TTS TTFA with a standard `GET /metrics` scrape endpoint and frontend waterfall latency charts.
- **Multilingual Support (English + Hindi + Hinglish) (`v0.14.0`)**: Real-time code-switching detection and technical vocabulary preservation.
- **Agent Tool Calling & Python Sandbox (`v0.13.0`)**: Mid-interview code execution and automated Mermaid architecture diagram generation.
- **Conversational Memory & Contradiction Detection (`v0.12.0`)**: Cross-turn continuity callbacks and candidate profile tracking.
- **Knowledge Base RAG (`v0.11.0`)**: Verification against company engineering standards.
- **Evidence-Based Evaluation (`v0.10.0`)**: Verbatim quote citations and technical red flag audits.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11/3.13, LiveKit API, WebSockets, Pytest, Motor / PyMongo
- **Frontend**: React, Vite, TypeScript, Vanilla HSL CSS
- **Voice Providers**: Deepgram (STT/TTS), OpenAI & Gemini (LLM), ElevenLabs (TTS)
- **Database**: MongoDB Atlas

---

## 📝 Technical Decisions & Version Docs

- [ADR-001: Project Foundation Stack & Architecture](docs/decisions/ADR-001-project-foundation.md)
- [ADR-002: Modular Voice Provider Abstractions & LiveKit Pipeline](docs/decisions/ADR-002-voice-pipeline.md)
- [ADR-003: Realtime Streaming Pipeline & Clause-Boundary Chunking](docs/decisions/ADR-003-streaming.md)
- [ADR-004: Voice Activity Detection & Natural Turn Taking](docs/decisions/ADR-004-turn-detection.md)
- [ADR-005: Real-time Barge-In & Audio Track Cancellation](docs/decisions/ADR-005-interruption-barge-in.md)
- [ADR-006: Interview Configuration, Prompt Construction & MongoDB Persistence](docs/decisions/ADR-006-interview-foundation.md)
- [ADR-007: Multi-Stage Interview State Machine](docs/decisions/ADR-007-interview-state-machine.md)
- [ADR-008: Adaptive Question Engine, Depth Probing & Topic Rotation](docs/decisions/ADR-008-adaptive-question-engine.md)
- [ADR-009: Multi-Dimensional Answer Evaluation & Cumulative Scorecard](docs/decisions/ADR-009-answer-evaluation.md)
- [ADR-010: Evidence-Based Evaluation, Quote Extraction & Red Flag Audits](docs/decisions/ADR-010-evidence-based-evaluation.md)
- [ADR-011: Knowledge Base Ingestion & Mid-Interview RAG Retrieval](docs/decisions/ADR-011-knowledge-base-rag.md)
- [ADR-012: Short-Term Cross-Turn Memory & Long-Term Candidate Profiling](docs/decisions/ADR-012-memory-cross-turn.md)
- [ADR-013: Mid-Interview Agent Tools, Code Sandbox & Architecture Visualizer](docs/decisions/ADR-013-agent-tools-and-actions.md)
- [ADR-014: Multilingual Support (English, Hindi & Hinglish) & Dynamic Code-Switching](docs/decisions/ADR-014-multilingual-support.md)
- [ADR-015: Observability, Distributed Turn Spans & Prometheus Metrics](docs/decisions/ADR-015-observability-telemetry.md)
- [ADR-016: Voice AI A/B Experimentation & Multi-Variant Evaluation](docs/decisions/ADR-016-ab-experimentation.md)
- [ADR-017: Golden Standard Evaluation Benchmark Suite & Scoring Calibration](docs/decisions/ADR-017-evaluation-benchmark-suite.md)
