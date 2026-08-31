# ADR-012: Short-Term Cross-Turn Memory & Long-Term Candidate Profiling

## Status
Accepted (v0.12.0)

## Context
Technical interviews require continuous conversational context and long-term memory. Within a session, an interviewer must recall earlier statements made by the candidate (e.g. past project architectures, databases chosen, concurrency patterns), synthesize natural cross-turn references (*"Earlier in past projects you mentioned using Kafka..."*), and detect contradictions when claims conflict. Across multiple interview rounds (e.g. Round 1 screening, Round 2 deep-dive), the system must track candidate progression and avoid asking duplicate questions.

## Decision
1. **Short-Term Working Memory Architecture**:
   - `ClaimEntity`: Captures specific architectural choices (`topic`, `statement`, `turn_index`, `stage`).
   - `InterviewMemoryEngine`: Extracts technologies (Postgres, MySQL, MongoDB, Redis, Kafka, Lock types, Kubernetes) and stores them in `ShortTermMemory`.
   - **Contradiction Detection**: Compares new statements against earlier claims (e.g. claiming pure NoSQL after earlier asserting Postgres relational ACID).
   - **Cross-Turn Callback Synthesis**: Dynamically weaves earlier claims into interviewer prompts.

2. **Long-Term Multi-Round Candidate Profiling**:
   - `CandidateProfile`: Tracks candidate interview history across sessions, round numbers, cumulative strengths/weaknesses, and previously asked questions.
   - `CandidateProfileRepository`: Aggregates multi-round candidate performance and provides longitudinal hiring signals.

3. **REST APIs & WebSocket Integration**:
   - `GET /api/interview/session/{session_id}/memory`: Inspects working claims and contradictions.
   - `GET /api/interview/candidate/{candidate_id}/profile`: Multi-round candidate profile.
   - Emits `contradiction_detected` WebSocket event.

4. **Frontend Working Memory UI**:
   - Live Memory Pill in HUD (`🧠 Memory: X Claims`).
   - Contradiction Warning Alert Banner.

## Consequences
### Positive
- Prevents candidates from giving inconsistent answers across different interview stages.
- Creates a remarkably natural, attentive interviewer persona that remembers prior context.
- Streamlines multi-round interview workflows for hiring teams.

### Tradeoffs
- Contradiction heuristics must balance sensitivity to avoid flagging legitimate architectural trade-offs as contradictions.
