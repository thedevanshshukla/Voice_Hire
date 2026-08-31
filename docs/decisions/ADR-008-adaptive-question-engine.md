# ADR-008: Adaptive Question Engine, Depth Probing & Topic Rotation

## Status
Accepted (v0.8.0)

## Context
Static question checklists create repetitive, rigid interviews that fail to evaluate actual candidate competencies. When a candidate gives a superficial answer (e.g. *"We used Redis for caching"*), a human interviewer immediately probes the mechanics (*"How did you handle cache stampede and TTL invalidation?"*). Conversely, when a candidate demonstrates mastery, the interviewer should not linger on basic questions but escalate complexity or advance to the next technical topic.

## Decision
1. **Answer Depth Heuristic & Evaluation**:
   - Implemented `AnswerDepth` classification (`SHALLOW_OR_VAGUE`, `MODERATE`, `STRONG_OR_COMPREHENSIVE`, `INCORRECT_OR_CONFUSED`) in `backend/app/interview/adaptive_engine.py`.
   - Analyzes response length, technical terminology (trade-offs, failure modes, metrics), and vague keyword drops.

2. **Specialized Technical Knowledge Probes**:
   - Built a repository of technical probes across key domains:
     - **Caching**: Cache stampede, thundering herd, TTL expiry spikes, invalidation consistency, multi-region write-through.
     - **Databases**: Index selectivity (B-Tree vs Hash vs GIN), EXPLAIN ANALYZE, MVCC table bloat, serialization anomalies.
     - **Concurrency**: Optimistic versioning vs pessimistic locks vs CAS, deadlock prevention, MESI cache coherence.
     - **Queues**: Partition distribution, consumer rebalances, idempotency under at-least-once delivery.
     - **Sharding**: Shard key selection, cross-shard joins, 2PC vs Saga orchestration.

3. **Dynamic Prompt Conditioning**:
   - `AdaptiveQuestionEngine` generates an `AdaptiveAction` containing an explicit `[ADAPTIVE DIRECTIVE]` injected into `InterviewPromptBuilder`.

4. **Dynamic Topic Rotation & Difficulty Scaling**:
   - Rotates through `config.topics` when sufficient depth is demonstrated (>= 2 turns in current topic or comprehensive response).
   - Adjusts difficulty scale from 1 (fundamentals) to 5 (principal).

5. **Real-time Adaptive HUD**:
   - WebSocket emits `adaptive_action` and frontend `VoiceRoom.tsx` renders live strategy pills and topic coverage indicators.

## Consequences
### Positive
- Prevents candidates from passing with memorized buzzwords by forcing mechanical explanations.
- Rewards strong candidates with higher difficulty and faster topic progression.
- Maintains balanced coverage across all selected technical domains.

### Tradeoffs
- Requires fine-tuned prompt directives so the LLM challenges the candidate constructively without becoming adversarial.
