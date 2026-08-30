# ADR-001: Project Foundation Stack & Architecture

## Problem
We need to establish a robust, modular, and maintainable project foundation for VoiceHire (a realtime Voice AI technical interviewer). This foundation needs to support local development, containerization, structured configuration, and provide a clear separation of concerns between backend (API & intelligence) and frontend (user interface).

## Options

### Option 1: Monolithic Python App with Templating (e.g., FastAPI + Jinja2)
* **Pros**: Simpler deployment, single language repository, no CORS configuration issues.
* **Cons**: Poor separation of concerns, harder to build premium interactive UI components required for voice visualization and real-time candidate interactions.

### Option 2: Split Backend (FastAPI) and Frontend (Next.js) Monorepo
* **Pros**: Complete separation of frontend and backend. Next.js offers standard SSR/SSG.
* **Cons**: Overhead of Next.js configurations, slower build times, and complex Docker multi-stage setups for simple SPA landing pages.

### Option 3: Split Backend (FastAPI) and Frontend (Vite + React + TS) Monorepo (Chosen)
* **Pros**: 
  - Complete separation of UI presentation from core voice and LLM logic.
  - FastAPI is lightweight, highly performant, handles async effortlessly, and aligns with LiveKit Agents SDK.
  - Vite offers extremely fast build/hot-reload times, standard TypeScript template, and packages cleanly into a small SPA served by Nginx.
  - Keeps local and Docker setups clean.

## Chosen Approach
We chose **Option 3** (FastAPI backend + Vite React TS frontend in a monorepo structure). 

## Reasoning
* **FastAPI**: It is the industry standard for Python asynchronous web frameworks. It integrates seamlessly with `pydantic-settings` for clean configuration and `logging` for structured system monitoring. It is ideal for running the LiveKit Agents worker loop in subsequent phases.
* **Vite + React + TypeScript**: Standard SPA setup with modern tooling. It compiles down to simple static assets that can be served via a lightweight Nginx container, keeping production builds small and secure.
* **Vanilla CSS**: We are using custom Vanilla CSS variables, gradients, and micro-animations to achieve the premium aesthetic required, bypassing the overhead and default look of utility frameworks like Tailwind unless requested.

## Tradeoffs
* Running two services requires orchestrating ports (`8000` for backend, `80`/`5173` for frontend) and configuring Cross-Origin Resource Sharing (CORS) on the backend.
* Docker Compose is required to streamline orchestration, increasing initial dev setup slightly but ensuring consistency across platforms.

## Consequences
* All future core features (STT, TTS, LiveKit connection) will be implemented as modular services inside the `backend/` component.
* The frontend will communicate asynchronously via HTTP (and WebSockets/WebRTC in future phases) to standard APIs exposed by FastAPI.
* Dev instructions must specify launching both frontend and backend or using Docker Compose.
