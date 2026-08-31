# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct structured, adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, an adaptive question engine with depth probing, and evidence-based evaluations with verbatim transcript quote citations.

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
- [x] **`v0.10.0` (Evidence-Based Evaluation)** ── *Current Release*
- [ ] `v0.11.0` (Knowledge Base & RAG)
- [ ] `v0.12.0` (Memory)
- [ ] `v0.13.0` (Agent Tools / Actions)
- [ ] `v0.14.0` (Multilingual support: English + Hindi)
- [ ] `v0.15.0` (Observability)
- [ ] `v0.16.0` (Voice AI Experimentation)
- [ ] `v0.17.0` (Evaluation Suite)
- [ ] `v0.18.0` (Reliability & Security)
- [ ] `v0.19.0` (Scale & Load Testing)
- [ ] `v1.0.0` (Final Production Polish)

---

## 🏗️ Architecture (v0.10.0)

```
                    ┌──────────────────────────────┐
                    │      Candidate Browser       │
                    │   React / Vite / TypeScript  │
                    │  - Evidence & Red Flags Tab  │
                    │  - Verbatim Quotation Cards  │
                    │  - Live Scorecard Modal      │
                    │  - Adaptive Strategy HUD     │
                    └──────────────┬───────────────┘
                                   │
                      WebSocket / REST / WebRTC
                                   │
                    ┌──────────────▼───────────────┐
                    │       FastAPI Backend        │
                    │  - /api/interview/.../score  │
                    │  - /api/interview/.../evid.  │
                    │  - WS /api/voice/stream/ws   │
                    └──────────────┬───────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
     │ Interview   │        │ Adaptive    │        │ Evidence    │
     │ State       │        │ Question    │        │ Evaluation  │
     │ Machine     │        │ Engine      │        │ Engine      │
     │ (6 Stages)  │        │ (Probing)   │        │ (Citations) │
     └─────────────┘        └─────────────┘        └─────────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │ Persists Evidence & Scorecards
                    ┌──────────────▼───────────────┐
                    │        MongoDB Atlas         │
                    │   - Transcripts + Quotes     │
                    │   - Red Flags & Decisions    │
                    └──────────────────────────────┘
```

---

## ✨ Features (v0.10.0)

- **Verbatim Transcript Quote Citations**: Automatically backs every strength and gap with direct candidate quotation snippets.
- **Technical Red Flag Detection**: Flags unsupported claims, fatal architectural misconceptions (e.g. zero-latency distributed ACID), and network failure ignorance.
- **Confidence Scoring & Executive Recommendations**: Computes evaluation confidence (0.0 to 1.0) and generates an executive hire/no-hire decision report.
- **5-Dimensional Answer Evaluation**: Automatically scores responses across *Correctness*, *Depth & Mechanics*, *Trade-off Awareness*, *Practical vs Theory*, and *Communication Clarity*.
- **Adaptive Question Engine**: Dynamic depth analysis and specialized mechanical follow-up probes.
- **6-Stage Interview State Machine**: Structured progression through `Intro -> Past Projects -> Core Technical -> System Design -> Candidate Q&A -> Wrap-Up`.
- **Real-time Barge-In & Interruption**: Interrupt the AI interviewer naturally mid-sentence with sub-200ms audio cancellation.
- **MongoDB Session Persistence**: Stores configured sessions, live transcripts with evaluated depth tags, turn counts, and evidence reports.

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
