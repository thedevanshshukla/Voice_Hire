# VoiceHire

### Realtime AI Technical Interviewer

VoiceHire is a production-oriented realtime Voice AI technical interviewer designed to conduct adaptive technical interviews for software developers. Powered by LiveKit, FastAPI, React, and advanced LLM orchestrations, it goes beyond simple speech-to-text queries to implement natural turn-taking, barge-in detection, and objective, evidence-based evaluations based on candidate responses.

---

## 🗺️ Version Progression

- **`v0.1.0` (Project Foundation)** ── *You are here*
- `v0.2.0` (Basic Voice Pipeline)
- `v0.3.0` (Realtime / Streaming)
- `v0.4.0` (Natural Turn Taking)
- `v0.5.0` (Interruption & Barge-In)
- `v0.6.0` (Interview Foundation)
- `v0.7.0` (Interview State Machine)
- `v0.8.0` (Adaptive Question Engine)
- `v0.9.0` (Answer Evaluation)
- `v0.10.0` (Evidence-Based Evaluation)
- `v0.11.0` (Knowledge Base & RAG)
- `v0.12.0` (Memory)
- `v0.13.0` (Agent Tools / Actions)
- `v0.14.0` (Multilingual support: English + Hindi)
- `v0.15.0` (Observability)
- `v0.16.0` (Voice AI Experimentation)
- `v0.17.0` (Evaluation Suite)
- `v0.18.0` (Reliability & Security)
- `v0.19.0` (Scale & Load Testing)
- `v1.0.0` (Final Production Polish)

---

## 🏗️ Architecture (v0.1.0)

```
                    ┌──────────────────────┐
                    │      Candidate       │
                    │    Browser (SPA)     │
                    └──────────┬───────────┘
                               │
                         HTTP / CORS
                               │
                    ┌──────────▼───────────┐
                    │    FastAPI Server    │
                    │    /health Check     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    Structured Log    │
                    │      (Console)       │
                    └──────────────────────┘
```

---

## ✨ Features

- **Decoupled Monorepo Structure**: Separate presentation layer (`frontend`) and API worker layer (`backend`).
- **Structured JSON Logging**: Observability ready for production tracking (standard JSON dumps in production; clean console prints for local debugging).
- **Environment Management**: Unified settings management using Pydantic Settings validator.
- **Micro-Animated UI**: Sleek, modern, dark-themed dashboard styled with high-performance CSS and live API health polling.
- **Docker Ready**: Containers for both FastAPI and React static distribution via Nginx.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11, Pydantic Settings, Uvicorn
- **Frontend**: React, Vite, TypeScript, Vanilla HSL CSS
- **Orchestration**: Docker, Docker Compose, Nginx (prod server)

---

## 🚀 Setup & Local Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ (with npm)
- Docker & Docker Compose (optional)

### Setup Configurations
Initialize local environment file:
```bash
cp .env.example .env
```

### Option A: Local Development Run

1. **Start Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --port 8000
   ```
   Backend will be running at [http://localhost:8000](http://localhost:8000). Verify status at [http://localhost:8000/health](http://localhost:8000/health).

2. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend will run at [http://localhost:5173](http://localhost:5173).

### Option B: Docker Compose Run (Production Sim)

Spin up backend and Nginx-served frontend:
```bash
docker-compose up --build -d
```
Access the dashboard at [http://localhost](http://localhost) (port 80). The backend runs at [http://localhost:8000](http://localhost:8000).

---

## 📝 Technical Decisions (ADRs)

- [ADR-001: Project Foundation Stack & Architecture](docs/decisions/ADR-001-project-foundation.md)
