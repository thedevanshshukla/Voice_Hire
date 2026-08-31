# ADR-007: Multi-Stage Interview State Machine

## Status
Accepted (v0.7.0)

## Context
A professional technical interview is not a random sequence of questions; it follows a structured arc from introduction, past project exploration, deep technical conceptual probing, scalable system architecture, and candidate questions, to wrap-up. To ensure comprehensive coverage within target time budgets (e.g. 30 minutes), VoiceHire requires a finite state machine managing stage progression, time allocations, and prompt directives.

## Decision
1. **6-Stage Sequential Architecture**:
   - `GREETING` (10% time budget, 1-2 turns): Introduction and format setup.
   - `RESUME_DEEP_DIVE` (20% time budget, 2-3 turns): Past architectural contributions, bottlenecks, and stack choices.
   - `CORE_CONCEPTS` (35% time budget, 3-5 turns): Deep conceptual probing into selected technical domains (DBMS, OS, Concurrency, APIs).
   - `SYSTEM_DESIGN` (25% time budget, 2-4 turns): Scenario-based scaling, caching, sharding, and fault tolerance.
   - `CANDIDATE_QUESTIONS` (7% time budget, 1-2 turns): Inviting and answering candidate questions.
   - `WRAP_UP` (3% time budget, 1 turn): Debrief, next steps, and professional closing.

2. **State Machine Engine**:
   - Implemented `InterviewStateMachine` in `backend/app/interview/state_machine.py`.
   - Dynamically calculates turn limits and duration minutes proportional to `config.duration_minutes`.
   - Evaluates transition criteria based on turn limits and candidate conversational triggers.

3. **Stage-Aware System Prompt Directives**:
   - `InterviewPromptBuilder` injects stage-specific behavioral constraints into each LLM turn, guiding the agent when to probe deeper vs when to transition.

4. **Real-time Stage Progression Synchronization**:
   - WebSocket `/api/voice/stream/ws` emits `stage_transition` events.
   - Frontend `VoiceRoom.tsx` renders an interactive 6-step progress timeline with active step highlighting and completion status.

## Consequences
### Positive
- Guarantees balanced technical evaluation covering fundamentals, past experience, and architectural depth.
- Prevents interviews from stalling in the intro or exceeding time limits on a single topic.
- Candidates receive a transparent, predictable interview flow visualized on their screen.

### Tradeoffs
- Rapid state machine progression requires the LLM to transition topics smoothly without abrupt tonal shifts.
