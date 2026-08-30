# VOICEHIRE — MASTER PROJECT SPECIFICATION

## 0. Role

You are the lead engineer responsible for building **VoiceHire**, a production-oriented realtime Voice AI technical interviewer.

Build the system incrementally and maintain it as a real software project.

The goal is NOT to create a simple "LLM + microphone" demo.

The final system should demonstrate practical expertise in:

* Voice AI
* realtime communication
* LiveKit
* STT
* TTS
* LLMs
* streaming
* VAD
* turn detection
* interruption / barge-in
* agentic workflows
* structured outputs
* RAG
* memory
* tool calling
* APIs
* backend engineering
* observability
* evaluation
* latency optimization
* reliability
* deployment
* experimentation

The project must be suitable as a serious **proof-of-work GitHub repository for a Voice AI engineering role**.

---

# 1. PRODUCT

Build a realtime AI technical interviewer.

A candidate should be able to:

1. Select an interview role.
2. Select difficulty/experience level.
3. Provide/paste a job description.
4. Select interview topics.
5. Select language:

   * English
   * Hindi
6. Start a realtime voice interview.
7. Talk naturally with the interviewer.
8. Interrupt the interviewer when necessary.
9. Receive dynamically generated questions.
10. Receive follow-up questions based on previous answers.
11. Be challenged when answers are incomplete or questionable.
12. Complete the interview.
13. Receive an evidence-based evaluation.
14. View transcript, scores, strengths, weaknesses and recommendations.
15. Review previous interviews.

The interviewer must NOT simply follow a fixed list of questions.

It should maintain interview state and adapt the conversation based on:

* candidate answers
* detected concepts
* answer quality
* missing concepts
* previous questions
* interview objectives
* remaining interview time

---

# 2. INITIAL SCOPE

Initial supported languages:

* English
* Hindi

The candidate explicitly selects the language before starting.

Do NOT implement Hinglish in V1.

Do NOT implement automatic language switching in V1.

Do NOT implement regional Indian languages initially.

The architecture should, however, make future multilingual support possible.

---

# 3. CORE TECHNOLOGY

Use **LiveKit Agents** as the primary realtime Voice AI framework.

Primary stack:

### Backend

* Python
* FastAPI
* LiveKit Agents
* MongoDB

### Realtime

* LiveKit
* WebRTC
* realtime audio tracks
* streaming media

### Voice

* STT provider abstraction
* TTS provider abstraction
* VAD
* turn detection
* interruption / barge-in

### Intelligence

* LLM provider abstraction
* structured outputs
* agentic workflow
* tool calling
* RAG
* memory

### Frontend

Use a modern React/Next.js frontend or another appropriate modern web stack.

### Infrastructure

* Docker
* environment-based configuration
* production-ready logging
* metrics
* tracing
* deployment-ready architecture

Do NOT introduce unnecessary technologies just for the sake of the resume.

Add Redis/Celery/Kafka/etc. only if a real architectural requirement emerges.

---

# 4. HIGH-LEVEL ARCHITECTURE

Target architecture:

```
                ┌──────────────────────┐
                │      Candidate       │
                │    Browser / Mic     │
                └──────────┬───────────┘
                           │
                        WebRTC
                           │
                ┌──────────▼───────────┐
                │       LiveKit        │
                │   Realtime Session   │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │    Voice Agent       │
                └──────────┬───────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
        STT               LLM               TTS
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                 Interview Controller
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   Question Engine     Evaluator          Memory
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                     Interview State
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
           RAG            Tools         Database
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                   Final Evaluation
                           │
                   ┌───────┴───────┐
                   ▼               ▼
              Dashboard        Report
```

Keep the architecture modular.

Voice transport, voice providers, LLM logic, interview logic, persistence and evaluation must not be tightly coupled.

---

# 5. DEVELOPMENT PHILOSOPHY

Build the system progressively.

DO NOT implement the complete system in one giant step.

Every phase must extend the previous phase.

The progression should be:

V0.1
↓
V0.2
↓
V0.3
↓
...
↓
V1.0

Every version must leave the previous functionality working.

Do not rewrite the entire architecture unnecessarily between versions.

Prefer incremental refactoring.

---

# 6. VERSION CONTROL

Use Git properly.

Branches:

* main
* develop
* feature/*

Workflow:

feature branch
↓
implementation
↓
tests
↓
documentation
↓
merge into develop
↓
validation
↓
merge into main
↓
Git tag

Version tags:

* v0.1.0
* v0.2.0
* v0.3.0
* ...
* v1.0.0

Never create a version tag until that version's acceptance criteria pass.

Use conventional commits where practical:

* feat:
* fix:
* refactor:
* test:
* docs:
* perf:
* chore:

Example:

feat(voice): add streaming TTS

fix(interruption): cancel active response on barge-in

docs(v0.4): document turn detection architecture

perf(voice): reduce first-audio latency

---

# 7. VERSION DOCUMENTATION

Maintain:

docs/
├── architecture/
├── decisions/
├── experiments/
├── versions/
│   ├── v0.1.md
│   ├── v0.2.md
│   ├── v0.3.md
│   └── ...
└── troubleshooting/

Every version document must contain:

1. Objective
2. Previous architecture
3. New architecture
4. Changes
5. Concepts introduced
6. Why those changes were required
7. Tests
8. Results
9. Known limitations
10. Next version

Maintain Architecture Decision Records:

docs/decisions/

Example:

ADR-001-livekit.md
ADR-002-voice-pipeline.md
ADR-003-streaming.md
ADR-004-turn-detection.md
ADR-005-memory.md
ADR-006-rag.md

Each ADR should explain:

* problem
* options
* chosen approach
* reasoning
* tradeoffs
* consequences

---

# 8. PHASE 0 — PROJECT FOUNDATION

Version: v0.1.0

Build:

* repository structure
* backend skeleton
* frontend skeleton
* configuration management
* environment variables
* basic health endpoint
* logging
* Docker setup
* Git workflow
* README
* development instructions

Do NOT implement interview logic yet.

Acceptance:

* backend starts
* frontend starts
* health endpoint works
* environment configuration works
* Docker build works
* README explains setup

---

# 9. PHASE 1 — BASIC VOICE PIPELINE

Version: v0.2.0

Build the smallest working Voice AI system.

Pipeline:

Microphone
↓
STT
↓
Text
↓
LLM
↓
Text
↓
TTS
↓
Audio

Use LiveKit Agents.

The user should be able to have a simple voice conversation.

No interview logic yet.

Learn/implement:

* audio input
* audio output
* STT
* TTS
* LLM
* LiveKit Agent basics

Acceptance:

* user can connect
* user speaks
* STT produces transcript
* LLM generates response
* TTS speaks response
* errors are handled gracefully

---

# 10. PHASE 2 — REALTIME / STREAMING

Version: v0.3.0

Upgrade the pipeline.

Implement:

* streaming STT
* streaming LLM responses where supported
* streaming TTS
* realtime audio delivery
* session management

Measure:

* STT latency
* LLM TTFT
* TTS first-audio latency
* total response latency

Create a basic latency logger.

Acceptance:

* response begins before full response generation completes where possible
* latency metrics are recorded
* streaming failures are handled

---

# 11. PHASE 3 — NATURAL TURN TAKING

Version: v0.4.0

Implement:

* VAD
* speech start detection
* speech end detection
* turn detection
* endpointing
* configurable silence thresholds

The system must distinguish between:

"candidate temporarily paused"

and

"candidate finished speaking."

Test:

* short pauses
* long pauses
* fast speech
* slow speech
* background noise
* incomplete sentences

Record turn detection metrics.

---

# 12. PHASE 4 — INTERRUPTION / BARGE-IN

Version: v0.5.0

Implement natural interruption.

Example:

Agent:
"Redis is an in-memory..."

Candidate:
"Wait, I meant..."

Agent:
[stops immediately]

Implement:

* speech interruption detection
* TTS cancellation
* active response cancellation
* generation cancellation where supported
* barge-in handling
* preemptive generation if useful

Measure:

* interruption detection latency
* cancellation latency
* false interruption rate

Create an explicit interruption test suite.

This phase is critical.

---

# 13. PHASE 5 — INTERVIEW FOUNDATION

Version: v0.6.0

Now transform the generic voice agent into VoiceHire.

Add interview configuration:

* role
* experience level
* job description
* duration
* selected topics
* language

Example:

Role:
Backend Engineer

Level:
SDE-1

Topics:

* DBMS
* OS
* Networking
* Backend
* System Design

Language:
English

Create interview session persistence in MongoDB.

---

# 14. PHASE 6 — INTERVIEW STATE MACHINE

Version: v0.7.0

Implement explicit interview state.

Example:

START
↓
INTRO
↓
QUESTION
↓
LISTENING
↓
EVALUATING
↓
FOLLOW-UP?
├── YES → FOLLOW-UP
└── NO → NEXT TOPIC
↓
QUESTION
↓
END

Do NOT rely entirely on free-form LLM behavior.

The controller should own:

* interview state
* topic progression
* question count
* timing
* termination
* allowed actions

The LLM should operate within controlled boundaries.

---

# 15. PHASE 7 — ADAPTIVE QUESTION ENGINE

Version: v0.8.0

Build dynamic question selection.

Given:

* current topic
* candidate answer
* previous questions
* previous evaluations
* interview objectives

decide whether to:

* ask follow-up
* challenge an answer
* move to next concept
* change difficulty
* move to another topic

Question types:

* conceptual
* application
* why
* tradeoff
* debugging
* scenario
* counterexample
* deep dive

Prevent repeated questions.

Track questions already asked.

---

# 16. PHASE 8 — ANSWER EVALUATION

Version: v0.9.0

Implement structured evaluation.

Example:

{
"correctness": 0.82,
"depth": 0.71,
"clarity": 0.86,
"confidence": 0.78,
"missing_concepts": [],
"claims": [],
"follow_up_required": true
}

Evaluate:

* correctness
* depth
* clarity
* completeness
* reasoning
* technical understanding

Do NOT produce arbitrary scores without evidence.

Evaluation should reference the candidate's actual answer.

---

# 17. PHASE 9 — EVIDENCE-BASED EVALUATION

Version: v0.10.0

For every meaningful score, preserve evidence.

Example:

Claim:
"Redis is always faster than PostgreSQL."

Evaluation:
Incorrect overgeneralization.

Evidence:
Candidate explicitly claimed X.

Expected concept:
Database choice depends on workload and access pattern.

Store:

* candidate claim
* evaluation
* supporting transcript
* missing concept
* confidence

The final report must be explainable.

---

# 18. PHASE 10 — KNOWLEDGE BASE / RAG

Version: v0.11.0

Create an interview knowledge base.

Topics:

* DBMS
* OS
* networking
* distributed systems
* Redis
* Kafka
* APIs
* backend
* system design

Implement:

* ingestion
* chunking
* embeddings
* retrieval
* optional reranking
* metadata filtering
* grounded evaluation

Use RAG to support:

* question generation
* concept verification
* evaluation
* follow-up generation

Do not blindly retrieve everything.

Retrieval must be relevant to the current interview state.

---

# 19. PHASE 11 — MEMORY

Version: v0.12.0

Implement three levels of memory.

### Short-term

Recent conversation context.

### Interview state

Structured:

* questions
* answers
* topics
* scores
* weaknesses
* strengths
* claims
* follow-ups

### Candidate history

Previous interviews and performance.

Do not use a vector database for everything.

Choose appropriately between:

* conversation context
* structured MongoDB data
* semantic retrieval

---

# 20. PHASE 12 — TOOLS / AGENT ACTIONS

Version: v0.13.0

Implement controlled tools such as:

get_candidate_profile()
get_interview_history()
retrieve_knowledge()
retrieve_question()
save_answer()
save_evaluation()
update_interview_state()
end_interview()
generate_report()

Tools must have:

* schemas
* validation
* error handling
* authorization boundaries
* deterministic behavior where possible

The LLM should not directly mutate important state without going through controlled tools.

---

# 21. PHASE 13 — ENGLISH + HINDI

Version: v0.14.0

Add language selection:

English
Hindi

The selected language controls:

* system prompts
* STT configuration
* LLM output
* TTS
* interviewer UI
* evaluation/report language where appropriate

No Hinglish.

No automatic language switching.

Architecture should allow future language providers.

Test Hindi independently for:

* transcription
* response quality
* TTS quality
* latency
* evaluation correctness

---

# 22. PHASE 14 — OBSERVABILITY

Version: v0.15.0

Add production-grade observability.

Every interview should have:

* interview ID
* session ID
* turn ID

Track:

* STT latency
* LLM TTFT
* LLM total latency
* TTS latency
* first audio latency
* total perceived latency
* interruptions
* tool calls
* errors
* retries
* token usage
* estimated cost

Use structured logs.

Add tracing where appropriate.

Make it possible to investigate a single bad interview turn.

---

# 23. PHASE 15 — VOICE AI EXPERIMENTATION

Version: v0.16.0

Create an experimentation framework.

Provider abstraction should allow testing different:

STT
LLM
TTS

without rewriting the interview system.

Benchmark:

* latency
* transcription quality
* response quality
* TTS quality
* interruption behavior
* cost

Create experiment reports.

Example:

Experiment:
STT provider comparison

Metrics:

* WER
* latency
* partial transcript speed
* final transcript accuracy

All benchmark numbers must come from actual experiments.

Never fabricate metrics.

---

# 24. PHASE 16 — VOICE AI EVALUATION SUITE

Version: v0.17.0

Create automated evaluation.

Test:

### Voice

* STT accuracy
* turn detection
* interruption handling
* latency

### Interview intelligence

* question relevance
* follow-up quality
* evaluation correctness
* hallucination
* consistency

Create a reproducible evaluation dataset.

Run the evaluator against fixed conversations.

Track regressions between versions.

---

# 25. PHASE 17 — RELIABILITY + SECURITY

Version: v0.18.0

Implement:

* retries
* timeouts
* provider failures
* graceful degradation
* session recovery
* API rate limiting
* authentication
* authorization
* input validation
* secret management
* prompt injection protection
* tool abuse protection

Test failure scenarios deliberately.

Examples:

* STT unavailable
* LLM timeout
* TTS timeout
* LiveKit disconnect
* database unavailable
* malformed tool arguments
* malicious candidate input

---

# 26. PHASE 18 — SCALE

Version: v0.19.0

Test concurrent interviews.

Target experiments:

* 1 concurrent interview
* 10
* 25
* 50
* 100 where infrastructure permits

Measure:

* CPU
* memory
* latency
* worker utilization
* API limits
* database performance
* failure rate

Identify bottlenecks.

Do not add distributed infrastructure unless benchmarks justify it.

---

# 27. PHASE 19 — FINAL PRODUCT

Version: v1.0.0

Polish the complete system.

Frontend:

### Setup

* role
* JD
* experience
* topics
* language
* duration

### Interview

* realtime connection state
* microphone state
* interviewer status
* timer
* transcript
* end interview

### Results

* overall score
* category scores
* strengths
* weaknesses
* evidence
* recommendations
* transcript
* interview history

The UI should feel like a real product, not a developer demo.

---

# 28. FINAL ARCHITECTURE GOAL

By v1.0, target something conceptually similar to:

Frontend
│
├── REST/WebSocket/API
│
▼
FastAPI
│
├─────────────── MongoDB
│
▼
Interview Service
│
▼
LiveKit Agent
│
├── VAD
├── Turn Detection
├── STT
├── LLM
├── TTS
├── Memory
├── Tools
└── RAG
│
▼
Evaluation
│
▼
Final Report

Observability should span the entire system.

---

# 29. TESTING REQUIREMENTS

Every phase must include appropriate tests.

At minimum:

### Unit tests

* state transitions
* evaluation parsing
* tool validation
* scoring logic
* configuration

### Integration tests

* STT
* LLM
* TTS
* database
* LiveKit session
* tools

### Voice tests

* pauses
* interruptions
* background noise
* long answers
* short answers
* rapid speech

### End-to-end tests

Full interview from:

setup
→ connection
→ questions
→ answers
→ follow-ups
→ evaluation
→ report

---

# 30. CODE QUALITY REQUIREMENTS

Follow:

* type hints
* modular architecture
* clear interfaces
* dependency injection where useful
* configuration management
* structured logging
* meaningful error handling
* tests
* documentation

Avoid:

* giant files
* giant functions
* duplicated provider code
* hardcoded API keys
* hardcoded interview questions
* magic numbers
* unnecessary abstractions
* unnecessary microservices

Prefer simple architecture until complexity is justified.

---

# 31. PROVIDER ABSTRACTION

Do not hardcode the project around one provider.

Create interfaces/adapters for:

STT
LLM
TTS

Example conceptual structure:

voice/
├── stt/
│   ├── base.py
│   └── providers/
├── tts/
│   ├── base.py
│   └── providers/
└── llm/
├── base.py
└── providers/

This allows experiments without changing interview logic.

---

# 32. DO NOT OVER-ENGINEER

Do not introduce:

* Kafka
* Kubernetes
* microservices
* Redis
* Celery
* vector databases
* multiple agent frameworks

unless a concrete requirement or benchmark justifies them.

The objective is to demonstrate engineering judgment, not maximum technology count.

---

# 33. CONTENT / PROOF-OF-WORK REQUIREMENTS

The repository should naturally generate technical content.

For each important experiment/document:

docs/experiments/

Examples:

* Why voice agents feel slow
* STT latency comparison
* TTS latency comparison
* Streaming vs non-streaming
* VAD vs turn detection
* How barge-in works
* Voice agent architecture
* RAG for technical interviews
* LLM evaluator reliability
* Voice AI cost analysis

Each article should contain:

Problem
→ Approach
→ Experiment
→ Results
→ Failure cases
→ Conclusion

Do not create generic AI-generated articles.

Base technical content on actual implementation and experiments.

---

# 34. README REQUIREMENTS

Final README must immediately communicate:

# VoiceHire

Realtime AI Technical Interviewer

One-paragraph explanation.

Then:

* live demo
* demo video
* architecture
* features
* technology stack
* version history
* benchmarks
* experiments
* evaluation
* setup
* deployment
* technical decisions

Include a visual architecture diagram.

Include a version progression:

v0.1 → Foundation
v0.2 → Voice pipeline
v0.3 → Streaming
v0.4 → Turn detection
v0.5 → Barge-in
...
v1.0 → Production

---

# 35. CRITICAL AGENT INSTRUCTION

You are allowed to implement the project autonomously, but **you must implement it phase-by-phase**.

Never jump directly to v1.0.

For the current phase:

1. Inspect existing repository.
2. Understand previous version.
3. Implement only the requested phase.
4. Preserve existing functionality.
5. Add tests.
6. Update documentation.
7. Update architecture diagrams if required.
8. Update changelog.
9. Run tests.
10. Fix failures.
11. Show what changed.
12. Commit using a meaningful commit message.
13. Tag the version only when acceptance criteria pass.
14. Stop and wait for approval before starting the next phase.

Do not silently implement future phases.

Do not add features because they "might be useful later."

If a future phase requires architectural preparation, make the minimum clean abstraction necessary and document why.

---

# 36. CURRENT TASK

Start with **V0.1 — Project Foundation only**.

Before writing code:

1. Inspect the repository.
2. Create the proposed structure.
3. Explain the architecture briefly.
4. Implement V0.1.
5. Test it.
6. Document it.
7. Commit it.
8. Tag it as v0.1.0.

Then STOP.

Do not implement V0.2 or any Voice AI functionality yet.

The project should evolve through explicit versioned milestones.
