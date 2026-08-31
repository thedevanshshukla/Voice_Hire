# VoiceHire

### Realtime AI Technical Interviewer — Version 1.0.0 (Production Release)

VoiceHire is a production-grade realtime Voice AI technical interviewer designed to conduct structured, adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it implements natural turn-taking, sub-150ms barge-in interruption, adaptive question depth probing, evidence-based evaluations with verbatim quote citations, company Knowledge Base RAG, conversational memory, agent tool execution (Python sandboxing, Mermaid diagramming), multilingual English + Hindi + Hinglish support, Prometheus observability, online A/B experimentation, golden benchmark calibration, PII sanitization, and multi-room concurrent load simulation.

---

## 🗺️ Completed Roadmap (v1.0.0)

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
- [x] **`v0.17.0` (Evaluation Suite & Benchmark Runner)**
- [x] **`v0.18.0` (Reliability & Security: PII Redaction & Rate Limiting)**
- [x] **`v0.19.0` (Scale & Multi-Room Concurrent Load Testing)**
- [x] **`v1.0.0` (Final Production Polish & Official Release)** ── *Production Ready*

---

## 🏗️ Architecture (v1.0.0)

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
                    │  - GET /health & /metrics    │
                    │  - PII Sanitizer & Limiter   │
                    │  - /api/experiments/*        │
                    │  - /api/evaluation/*         │
                    │  - /api/scale/*              │
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

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11/3.13, LiveKit API, WebSockets, Pytest, Motor / PyMongo, NumPy
- **Frontend**: React, Vite, TypeScript, Vanilla HSL CSS
- **Voice Providers**: Deepgram (STT/TTS), OpenAI & Gemini (LLM), ElevenLabs (TTS)
- **Database**: MongoDB Atlas

---

## 🚀 Setup & Local Execution

### 1. Start Backend:
```bash
cd backend
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will run at [http://localhost:8000](http://localhost:8000).

### 2. Start Frontend:
```bash
cd frontend
npm install
npm run dev
```
Frontend will run at [http://localhost:5173](http://localhost:5173).

### 3. Run Test Suite:
```bash
cd backend
pytest tests
```

---

## 📝 Architecture Decisions (ADRs)

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
- [ADR-018: Reliability, PII Redaction & Sliding-Window Rate Limiting](docs/decisions/ADR-018-reliability-and-security.md)
- [ADR-019: Multi-Room Concurrent Load Simulation & Latency Distribution](docs/decisions/ADR-019-scale-and-load-testing.md)
- [ADR-020: VoiceHire v1.0.0 Production Release & System Integration](docs/decisions/ADR-020-production-release-v1.md)
