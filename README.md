# VoiceHire — Realtime AI Technical Interviewer

[![Version](https://img.shields.io/badge/version-1.0.0--prod-7c3aed.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-77%2F77%20passing-10b981.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-3b82f6.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/frontend-React%2018%20%2B%20TypeScript-61dafb.svg)](https://reactjs.org)

**VoiceHire** is an enterprise-grade, realtime Voice AI technical interviewer built to conduct structured, adaptive, and evidence-grounded engineering assessments. Powered by Deepgram Nova-2, ElevenLabs, OpenAI, FastAPI, MongoDB Atlas, and React TypeScript, it delivers natural turn-taking, noise-isolated audio recognition, sub-150ms barge-in interruptions, compulsory resume project deep-dives, calibrated multi-dimensional evaluations, and automated audit scorecards.

---

## 🌟 Key Features & Capabilities

### 🎙️ 1. Studio-Grade Voice Pipeline & Audio Isolation
- **Hardware Noise Suppression & Echo Cancellation**: Web Audio pipeline with automatic gain control, acoustic beamforming, and 48kHz Opus stream capture.
- **Deepgram Nova-2 Speech-to-Text**: Domain-specific technical keyword boosting (`PostgreSQL`, `Redis`, `Kafka`, `MVCC`, `B-Tree`, `Celery`, `Docker`, `Kubernetes`, `Deadlock`, etc.) eliminates phonetic slip-ups and ignores background ambient noise.
- **Zero Monologues**: Natural, spoken-voice responses constrained to 2–3 sentences with sentence-chunked synthesis and keep-alive heartbeats.

### 📄 2. Compulsory Resume & Context-Aware Question Generation
- **Mandatory Resume Deep-Dive**: Candidates must upload or paste their technical work history and project summaries before initiating assessments.
- **Scenario A (Resume + Job Description)**: The AI dynamically cross-references requirements from the JD with specific claims in the candidate's resume (e.g. evaluating how past database designs scale to meet the JD's high-throughput SLA).
- **Scenario B (Resume Only)**: The AI grounds 100% of technical questions in the candidate's actual projects, drilling progressively into internal mechanisms, architectural trade-offs, failure modes, and concurrency primitives until reaching the candidate's knowledge boundaries.
- **Single-Question Enforcement**: Eliminates numbered questionnaire dumps, asking strictly **one focused technical question per turn**.

### 📊 3. Calibrated 5-Dimensional Evaluation Engine
Evaluates candidate responses against strict industry engineering rubrics:
1. **Technical Correctness** (30% weight)
2. **Depth & Underlying Mechanics** (30% weight)
3. **Trade-off Awareness & Architecture Reasoning** (15% weight)
4. **Practical Production Reality vs Theory** (15% weight)
5. **Communication Clarity & Structure** (10% weight)

| Response Quality | Calibrated Score | Evaluation Verdict | Behavior |
| :--- | :---: | :---: | :--- |
| **Non-Answer / Silence / Gibberish** | **0.0 / 5.0** (0/10) | `NO_HIRE` | Silence timeout (5s), non-technical fragments, refusal. **Zero technical credit.** |
| **Superficial / Keywords Only** | **2.5 / 5.0** (5/10) | `NO_HIRE` | Mentions domain terms (*Redis*, *database*) without explaining mechanisms or design. |
| **Solid & Correct Fundamentals** | **3.8 / 5.0** (7.5/10) | `BORDERLINE` / `HIRE` | Technically accurate explanation with clear core fundamentals. |
| **Mastery & Production Reality** | **4.8 - 5.0 / 5.0** (9.5-10/10) | `STRONG_HIRE` | Exemplary grasp of internal mechanisms, trade-offs, and production edge-cases. |

### 🔒 4. Deterministic Session Language Consistency
- The interview language is strictly locked to the candidate's chosen language at setup (**English**, **Hindi**, or **Hinglish**).
- Prevents accidental mid-interview language flips caused by noisy speech transcription.

### ⏱️ 5. Sticky Header Controls & Instant Wrap-Up Report
- **Sticky Header**: Prominently displays the real-time session countdown timer, Recruiter Scorecard audit trigger, and **`⏹️ End Interview & View Report`** button that never scrolls away.
- **Automatic Wrap-Up**: Concluding statements automatically terminate the audio stream and navigate directly to the detailed assessment report (`/report/:sessionId`).

### 🗄️ 6. Enterprise Data Layer & User Authentication
- **User Authentication**: Secure JWT-based sign-in and registration (`/api/auth/register`, `/api/auth/login`) associating all sessions and reports under the recruiter/candidate email.
- **MongoDB Atlas Storage**: Persistent storage for session configurations, working short-term memory, cross-turn contradiction logs, and verbatim evidence citations.

---

## 🏗️ System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │            Candidate Browser            │
                    │        React / Vite / TypeScript        │
                    │  - Pure Voice Interface & Live Waveform │
                    │  - Sticky Timer & End Interview Button  │
                    │  - Independent Scrollable Transcripts   │
                    │  - Full Evaluation Scorecard & PDF Export│
                    └────────────────────┬────────────────────┘
                                         │
                         Opus WebM Audio / WebSocket / REST
                                         │
                    ┌────────────────────▼────────────────────┐
                    │             FastAPI Backend             │
                    │  - JWT Authentication & PII Sanitizer   │
                    │  - Deepgram Nova-2 STT Provider         │
                    │  - ElevenLabs / OpenAI TTS Provider     │
                    │  - GPT-4o / Gemini Pro LLM Provider     │
                    │  - Multi-Stage State Machine (6 Stages) │
                    │  - Answer Evaluator & Evidence Engine   │
                    └────────────────────┬────────────────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          ▼                              ▼                              ▼
 ┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
 │ MongoDB Atlas   │            │ Adaptive Engine │            │ Prometheus &    │
 │ - Users & Auth  │            │ - Depth Prober  │            │ Telemetry HUD   │
 │ - Sessions & DB │            │ - Topic Switcher│            │ - Latency Spans │
 │ - Transcripts   │            │ - Claim Tracker │            │ - TTFT / TTFA   │
 └─────────────────┘            └─────────────────┘            └─────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11 / 3.13), Uvicorn, Pydantic v2 |
| **Voice Processing** | Deepgram Nova-2 STT, ElevenLabs TTS, Web Audio API, Web Speech API |
| **LLM & Intelligence** | OpenAI (GPT-4o), Google Gemini Pro, Adaptive Interview FSM |
| **Frontend UI** | React 18, TypeScript, Vite, Vanilla HSL CSS Design System |
| **Database & Auth** | MongoDB Atlas, Motor / PyMongo, PyJWT, Passlib (Bcrypt) |
| **Testing & CI** | Pytest, pytest-asyncio, AnyIO, HTTPX ASGI Transport |

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB instance (local or Atlas URI)
- API Keys: `DEEPGRAM_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY` (optional)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/voice-hire.git
cd "voice hire"
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will start at **http://localhost:8000**. Interactive docs available at **http://localhost:8000/docs**.

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Frontend web application will run at **http://localhost:5173**.

### 4. Running the Test Suite
```bash
cd ../backend
pytest tests
```
*Executes all 77 unit, integration, and voice pipeline tests.*

---

## 📁 Repository Structure

```
voice-hire/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py                  # JWT Auth & User Endpoints
│   │   │   └── endpoints.py             # Voice Turn, Sessions, Reports & Telemetry
│   │   ├── interview/
│   │   │   ├── adaptive_engine.py       # Topic Rotation & Depth Prober
│   │   │   ├── evaluation_engine.py     # 5-Dimensional Calibrated Scorer
│   │   │   ├── evidence_engine.py       # Quote Extraction & Red Flag Auditor
│   │   │   ├── memory_engine.py         # Working Short-Term Memory & Contradiction Detection
│   │   │   ├── prompt_builder.py        # Single-Question & Resume/JD Cross-Referencing Prompts
│   │   │   └── state_machine.py         # 6-Stage Progression FSM (Greeting -> Wrap Up)
│   │   ├── voice/
│   │   │   ├── pipeline.py              # STT -> LLM -> TTS Turn Orchestration
│   │   │   ├── stt/providers/deepgram.py# Deepgram Nova-2 with Keyword Boosting
│   │   │   └── tts/providers/           # ElevenLabs & Fallback Providers
│   │   ├── db/
│   │   │   └── mongo.py                 # Async MongoDB Atlas Repositories
│   │   └── config.py                    # Environment & Provider Settings
│   └── tests/                           # 77 Pytest Test Cases
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthView.tsx             # Login & Registration Screens
│   │   │   ├── DashboardView.tsx        # Recruiter Assessment Dashboard & History
│   │   │   ├── InterviewSetup.tsx       # Compulsory Resume & Role Configuration
│   │   │   ├── ReportView.tsx           # Full Dimensional Breakdown & Transcripts
│   │   │   └── VoiceRoom.tsx            # Realtime Sticky Header Voice Interview Room
│   │   ├── context/
│   │   │   └── AuthContext.tsx          # JWT Auth State Management
│   │   ├── App.tsx                      # React Router Routing
│   │   └── index.css                    # Glassmorphism Design System Tokens
│   └── package.json
└── README.md
```

---

## 📄 Architecture Decisions (ADRs)

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
- [ADR-014: Multilingual Support (English, Hindi & Hinglish) & Language Locking](docs/decisions/ADR-014-multilingual-support.md)
- [ADR-015: Observability, Distributed Turn Spans & Prometheus Metrics](docs/decisions/ADR-015-observability-telemetry.md)
- [ADR-016: Voice AI A/B Experimentation & Multi-Variant Evaluation](docs/decisions/ADR-016-ab-experimentation.md)
- [ADR-017: Golden Standard Evaluation Benchmark Suite & Scoring Calibration](docs/decisions/ADR-017-evaluation-benchmark-suite.md)
- [ADR-018: Reliability, PII Redaction & Sliding-Window Rate Limiting](docs/decisions/ADR-018-reliability-and-security.md)
- [ADR-019: Multi-Room Concurrent Load Simulation & Latency Distribution](docs/decisions/ADR-019-scale-and-load-testing.md)
- [ADR-020: VoiceHire v1.0.0 Production Release & System Integration](docs/decisions/ADR-020-production-release-v1.md)

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for details.
