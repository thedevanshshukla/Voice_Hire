# ADR-009: Multi-Dimensional Answer Evaluation & Cumulative Scorecard

## Status
Accepted (v0.9.0)

## Context
Technical evaluations must provide clear, objective, and multi-dimensional signal rather than a subjective or vague impression. A candidate may communicate eloquently yet provide inaccurate or shallow mechanics; another may have deep production experience but present unstructured answers. VoiceHire requires a structured rubric evaluating every turn across core technical dimensions, persisting evaluations to MongoDB, and generating comprehensive scorecard analytics.

## Decision
1. **5-Dimensional Evaluation Rubric**:
   - `Correctness` (25% weight): Technical validity, accuracy of principles and syntax.
   - `Depth & Mechanics` (25% weight): Internal data structures, memory layout, system calls, network roundtrips, isolation guarantees.
   - `Trade-off Awareness` (20% weight): Explicit reasoning regarding downsides, CAP theorem trade-offs, storage vs compute.
   - `Practical Experience vs Theory` (15% weight): Operational evidence (metrics, alerts, outages, runbooks, canary deployments) vs rote theory.
   - `Communication Clarity` (15% weight): Structured, concise explanations vs rambling.

2. **Evaluation Engine Architecture**:
   - Implemented `AnswerEvaluator` in `backend/app/interview/evaluation_engine.py`.
   - Produces structured `TurnEvaluation` on every candidate turn.
   - Dynamically aggregates `SessionScorecard` computing running averages, pass/fail recommendation, deduplicated strengths, and areas for improvement.

3. **Database Persistence**:
   - `TranscriptEntry` stores `TurnEvaluation`.
   - `InterviewSession` persists cumulative `SessionScorecard` in MongoDB.

4. **Frontend Live Scorecard UI**:
   - Live turn score pill in HUD (`⭐ Score: 4.5/5.0`).
   - "📊 Scorecard" modal rendering 5-dimensional progress bars, overall verdict, strengths, and areas for growth.

## Consequences
### Positive
- Provides standardized, objective hiring signal for engineering managers and interviewers.
- Highlights specific dimensional gaps (e.g. strong fundamentals but missing production trade-offs).
- Enables candidates to review structured feedback for continuous growth.

### Tradeoffs
- Real-time turn scoring adds computational overhead, handled via asynchronous post-turn processing.
