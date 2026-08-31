# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, and objective, evidence-based evaluations based on candidate responses.

---

## 🗺️ Version Progression

- [x] **`v0.1.0` (Project Foundation)**
- [x] **`v0.2.0` (Basic Voice Pipeline)** ── *Current Release*
- [ ] `v0.3.0` (Realtime / Streaming)
- [ ] `v0.4.0` (Natural Turn Taking)
- [ ] `v0.5.0` (Interruption & Barge-In)
- [ ] `v0.6.0` (Interview Foundation)
- [ ] `v0.7.0` (Interview State Machine)
- [ ] `v0.8.0` (Adaptive Question Engine)
- [ ] `v0.9.0` (Answer Evaluation)
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

## 🏗️ Architecture (v0.2.0)

```
                    ┌──────────────────────────────┐
                    │      Candidate Browser       │
                    │   React / Vite / TypeScript  │
                    │  - VoiceRoom & Visualizer    │
                    │  - Realtime Transcript Feed  │
                    └──────────────┬───────────────┘
                                   │
                                WebRTC / REST
                                   │
                    ┌──────────────▼───────────────┐
                    │       FastAPI Backend        │
                    │  - /api/voice/token (JWT)    │
                    │  - /api/voice/turn (Pipeline)│
                    │  - /health & /voice/status   │
                    └──────────────┬───────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
     │ STT Provider│        │ LLM Provider│        │ TTS Provider│
     │ Deepgram    │        │ OpenAI      │        │ ElevenLabs  │
     │ Mock Local  │        │ Gemini/Mock │        │ Deepgram/Mck│
     └─────────────┘        └─────────────┘        └─────────────┘
```

---

## ✨ Features (v0.2.0)

- **Modular Voice Provider Abstractions**: Clean abstract interfaces and factory for STT (`Deepgram`, `Mock`), LLM (`OpenAI`, `Gemini`, `Mock`), and TTS (`ElevenLabs`, `Deepgram`, `Mock`).
- **LiveKit Session Token Generation**: Secure participant JWT authentication with room video grants.
- **Turn Orchestration & Latency Telemetry**: Per-turn diagnostics measuring STT latency, LLM latency, TTS latency, and total perceived roundtrip time.
- **Interactive Voice Room UI**: Full-featured React interview room with live audio visualizer, mic control, candidate/agent message stream, and audio playback.
- **Automated Test Suite**: 9 unit and integration tests verifying all provider abstractions, pipeline execution, and API endpoints.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11/3.13, LiveKit API, Pydantic v2, Pytest
- **Frontend**: React, Vite, TypeScript, Vanilla HSL CSS
- **Voice Providers**: Deepgram (STT/TTS), OpenAI & Gemini (LLM), ElevenLabs (TTS)
- **Orchestration**: Docker, Docker Compose, Nginx

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
- [Version 0.1.0 Release Notes](docs/versions/v0.1.md)
- [Version 0.2.0 Release Notes](docs/versions/v0.2.md)
