# ADR-010: Evidence-Based Evaluation, Quote Extraction & Red Flag Audits

## Status
Accepted (v0.10.0)

## Context
High-stakes hiring decisions require an audit trail of concrete evidence. Without verbatim citations, evaluations are prone to skepticism and subjective bias. Furthermore, interviewers must detect technical red flags — such as claiming senior expertise but struggling on fundamental follow-ups, or demonstrating dangerous architectural misconceptions (e.g. claiming zero latency across microservices or ignoring network partitions).

## Decision
1. **Verbatim Quote Citation Engine**:
   - Implemented `EvidenceEvaluator` in `backend/app/interview/evidence_engine.py`.
   - Extracts verbatim snippets (`EvidenceSnippet`) from candidate transcripts to back each identified strength and weakness.

2. **Automated Red Flag & Anti-Pattern Detection**:
   - `UNSUPPORTED_CLAIM`: Candidate claimed expert-level mastery in introductory stages but failed subsequent conceptual probes.
   - `FATAL_MISCONCEPTION`: Candidate claimed impossible trade-offs (e.g., zero-latency distributed transactions across microservices).
   - `FAILURE_IGNORANCE`: Assuming networks and distributed dependencies never fail (CAP theorem violation).
   - `SUPERFICIAL_BUZZWORD`: Dropping buzzwords without architectural mechanics.

3. **Confidence Scoring & Executive Recommendation**:
   - Computes `confidence_score` (0.0 to 1.0) based on evaluated sample size.
   - Formulates executive recommendation (`STRONG_HIRE`, `HIRE`, `BORDERLINE`, `NO_HIRE`) with reasoning.

4. **Frontend Evidence Audit UI**:
   - Added an Evidence & Red Flags tab in the Scorecard modal displaying quote citation cards (`💬 "..."`) and red flag severity badges.

## Consequences
### Positive
- Produces verifiable, audit-proof hiring reports with zero ambiguity.
- Immediately flags high-risk candidate assertions and unvetted claims.
- Accelerates hiring manager debriefs.

### Tradeoffs
- Quote extraction requires careful trimming to capture the core technical argument without transcript noise.
