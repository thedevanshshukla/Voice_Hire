# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct structured, adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, an adaptive question engine with depth probing, evidence-based evaluations, mid-interview Knowledge Base RAG grounded in company standards, and short-term / long-term conversational memory.

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
- [x] **`v0.12.0` (Memory & Cross-Turn Synthesis)** ── *Current Release*
- [ ] `v0.13.0` (Agent Tools / Actions)
- [ ] `v0.14.0` (Multilingual support: English + Hindi)
- [ ] `v0.15.0` (Observability)
- [ ] `v0.16.0` (Voice AI Experimentation)
- [ ] `v0.17.0` (Evaluation Suite)
- [ ] `v0.18.0` (Reliability & Security)
- [ ] `v0.19.0` (Scale & Load Testing)
- [ ] `v1.0.0` (Final Production Polish)

---

## 🏗️ Architecture (v0.12.0)

```
                    ┌──────────────────────────────┐
                    │      Candidate Browser       │
                    │   React / Vite / TypeScript  │
                    │  - Memory Claims HUD (🧠)    │
                    │  - Contradiction Alert (⚠️)   │
                    │  - Knowledge Base Drawer     │
                    │  - Live Scorecard & Evidence │
                    └──────────────┬───────────────┘
                                   │
                      WebSocket / REST / WebRTC
                                   │
                    ┌──────────────▼───────────────┐
                    │       FastAPI Backend        │
                    │  - /api/interview/memory     │
                    │  - /api/interview/candidate  │
                    │  - WS /api/voice/stream/ws   │
                    └──────────────┬───────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
     │ Memory &    │        │ Knowledge   │        │ Adaptive    │
     │ Profile     │ ──►   │ Base RAG    │ ◄──►   │ Question    │
     │ Engine      │        │ Engine      │        │ Engine      │
     └─────────────┘        └─────────────┘        └─────────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │ Persists Sessions, Claims & Profiles
                    ┌──────────────▼───────────────┐
                    │        MongoDB Atlas         │
                    │   - Working Memory Claims    │
                    │   - Multi-Round Profiles     │
                    └──────────────────────────────┘
```

---

## ✨ Features (v0.12.0)

- **Short-Term Conversational Memory**: Captures candidate architectural claims (databases, caches, lock choices, queues) and weaves natural cross-turn references into subsequent questions (*"Earlier in past projects you mentioned using Redis..."*).
- **Contradiction Detection**: Automatically detects conflicting claims made across turns (e.g. claiming Kafka earlier, but later asserting no message queues were used).
- **Long-Term Multi-Round Candidate Profiles**: Persists candidate scores, strengths, weaknesses, and previously asked questions across multiple rounds.
- **Knowledge Base Ingestion & RAG**: Ground questions and answer verification in official company engineering standards, custom question banks, and job rubrics.
- **Verbatim Transcript Quote Citations**: Automatically backs every strength and gap with direct candidate quotation snippets.
- **Technical Red Flag Detection**: Flags unsupported claims, fatal architectural misconceptions, and network failure ignorance.
- **5-Dimensional Answer Evaluation**: Automatically scores responses across *Correctness*, *Depth & Mechanics*, *Trade-off Awareness*, *Practical vs Theory*, and *Communication Clarity*.
- **Adaptive Question Engine**: Dynamic depth analysis and specialized mechanical follow-up probes.
- **6-Stage Interview State Machine**: Structured progression through `Intro -> Past Projects -> Core Technical -> System Design -> Candidate Q&A -> Wrap-Up`.
- **Real-time Barge-In & Interruption**: Interrupt the AI interviewer naturally mid-sentence with sub-200ms audio cancellation.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11/3.13, LiveKit API, WebSockets, Pytest, Motor / PyMongo
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
- [Version 0.1.0 Release Notes](docs/versions/v0.1.md)
- [Version 0.2.0 Release Notes](docs/versions/v0.2.md)
- [Version 0.3.0 Release Notes](docs/versions/v0.3.md)
- [Version 0.4.0 Release Notes](docs/versions/v0.4.md)
- [Version 0.5.0 Release Notes](docs/versions/v0.5.md)
- [Version 0.6.0 Release Notes](docs/versions/v0.6.md)
- [Version 0.7.0 Release Notes](docs/versions/v0.7.md)
- [Version 0.8.0 Release Notes](docs/versions/v0.8.md)
- [Version 0.9.0 Release Notes](docs/versions/v0.9.md)
- [Version 0.10.0 Release Notes](docs/versions/v0.10.md)
- [Version 0.11.0 Release Notes](docs/versions/v0.11.md)
- [Version 0.12.0 Release Notes](docs/versions/v0.12.md)
