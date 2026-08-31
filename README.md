# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct structured, adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, an adaptive question engine with depth probing, and multi-dimensional answer evaluation persisted to MongoDB.

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
- [x] **`v0.9.0` (Answer Evaluation Engine)** ── *Current Release*
- [ ] `v0.10.0` (Evidence-Based Evaluation)
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

## 🏗️ Architecture (v0.9.0)

```
                    ┌──────────────────────────────┐
                    │      Candidate Browser       │
                    │   React / Vite / TypeScript  │
                    │  - Live Scorecard Modal      │
                    │  - Turn Score Badges         │
                    │  - Adaptive Strategy HUD     │
                    │  - 6-Stage Visual Timeline   │
                    └──────────────┬───────────────┘
                                   │
                      WebSocket / REST / WebRTC
                                   │
                    ┌──────────────▼───────────────┐
                    │       FastAPI Backend        │
                    │  - /api/interview/session    │
                    │  - /api/interview/.../score  │
                    │  - WS /api/voice/stream/ws   │
                    └──────────────┬───────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
     │ Interview   │        │ Adaptive    │        │ Answer      │
     │ State       │        │ Question    │        │ Evaluation  │
     │ Machine     │        │ Engine      │        │ Engine      │
     │ (6 Stages)  │        │ (Probing)   │        │ (5 Dims)    │
     └─────────────┘        └─────────────┘        └─────────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │ Persists Turn Scores & Scorecard
                    ┌──────────────▼───────────────┐
                    │        MongoDB Atlas         │
                    │   - Transcripts + Scores     │
                    │   - Cumulative Scorecards    │
                    └──────────────────────────────┘
```

---

## ✨ Features (v0.9.0)

- **5-Dimensional Answer Evaluation**: Automatically scores responses across *Correctness* (25%), *Depth & Mechanics* (25%), *Trade-off Awareness* (20%), *Practical Experience vs Theory* (15%), and *Communication Clarity* (15%).
- **Turn-Level Scoring & Feedback**: Persists strengths, gaps, and coaching feedback on every transcript turn.
- **Cumulative Session Scorecards**: Computes running averages, hiring recommendations (*Strong Hire*, *Hire*, *Borderline*, *No Hire*), and top strengths/growth areas.
- **Frontend Scorecard Modal**: Interactive 5-dimensional breakdown with progress bars, verdict badge, and turn scores.
- **Adaptive Question Engine**: Dynamic depth analysis and specialized mechanical follow-up probes (Cache stampede, index selectivity, lock contention, Kafka rebalances).
- **6-Stage Interview State Machine**: Structured progression through `Intro -> Past Projects -> Core Technical -> System Design -> Candidate Q&A -> Wrap-Up`.
- **Real-time Barge-In & Interruption**: Interrupt the AI interviewer naturally mid-sentence with sub-200ms audio cancellation.
- **MongoDB Session Persistence**: Stores configured sessions, live transcripts with evaluated depth tags, turn counts, and scorecards.

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
- [Version 0.1.0 Release Notes](docs/versions/v0.1.md)
- [Version 0.2.0 Release Notes](docs/versions/v0.2.md)
- [Version 0.3.0 Release Notes](docs/versions/v0.3.md)
- [Version 0.4.0 Release Notes](docs/versions/v0.4.md)
- [Version 0.5.0 Release Notes](docs/versions/v0.5.md)
- [Version 0.6.0 Release Notes](docs/versions/v0.6.md)
- [Version 0.7.0 Release Notes](docs/versions/v0.7.md)
- [Version 0.8.0 Release Notes](docs/versions/v0.8.md)
- [Version 0.9.0 Release Notes](docs/versions/v0.9.md)
