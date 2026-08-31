# ADR-006: Interview Configuration, Prompt Construction & MongoDB Persistence

## Status
Accepted (v0.6.0)

## Context
Phase 0 through 4 developed a robust, low-latency, streaming Voice AI pipeline with turn-taking and barge-in capabilities. To fulfill VoiceHire's core mission as an AI Technical Interviewer, the system needs domain models representing structured technical interviews: customizable engineering roles, seniority expectations (SDE-1 through Staff), focus topics, job descriptions, and complete session persistence in MongoDB.

## Decision
1. **Interview Domain Models**:
   - Defined `InterviewRole`, `ExperienceLevel`, `InterviewTopic`, `InterviewLanguage`, `InterviewConfig`, and `InterviewSession` schemas in `backend/app/models/interview.py`.
   - Included structured transcripts (`TranscriptEntry`) capturing role, text, latency telemetry, and interruption flags.

2. **MongoDB Session Repository**:
   - Implemented `InterviewSessionRepository` in `backend/app/db/mongo.py` using `Motor` (`AsyncIOMotorClient`).
   - Built with an automated in-memory storage fallback to allow seamless offline local development and isolated unit test execution.

3. **Dynamic Prompt Builder**:
   - Implemented `InterviewPromptBuilder` in `backend/app/interview/prompt_builder.py`.
   - Assembles contextual interviewer system prompts enforcing:
     - Voice conversation brevity (2-3 sentences max).
     - One single question per turn.
     - Role & seniority calibrated depth (fundamentals for SDE-1 vs distributed consensus/trade-offs for Staff).
     - Target job description requirements and language instructions (English / Hindi).

4. **Interview Setup Wizard & History Drawer**:
   - React UI in `frontend/src/components/InterviewSetup.tsx` with role cards, experience level badges, topic multi-selector chips, and past interview history.

## Consequences
### Positive
- Transforms generic voice agent into a specialized technical interviewer.
- Complete interview sessions and latency diagnostics are recorded and queryable in MongoDB.
- System prompt construction automatically enforces voice AI best practices (e.g. preventing monologues).

### Tradeoffs
- Large raw job descriptions are truncated to 1000 characters to keep prompt overhead low and maintain fast TTFT (< 500ms).
