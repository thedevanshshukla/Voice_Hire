# ADR-011: Knowledge Base Ingestion & Mid-Interview RAG Retrieval

## Status
Accepted (v0.11.0)

## Context
Standard technical interviewers often rely on generic public knowledge rather than the hiring company's actual internal engineering standards, architectural failure guidelines, or specialized question banks. For example, a company may have strict standards regarding idempotency keys, write-through caching with early expiry, circuit breakers, or zero-downtime database migrations. VoiceHire requires a dynamic Knowledge Base & RAG Engine to ground interview evaluations in company-specific technical documents in real time.

## Decision
1. **Knowledge Ingestion Architecture**:
   - `KnowledgeCategory`: `COMPANY_STANDARDS`, `QUESTION_BANK`, `ARCHITECTURE_PATTERNS`, `JOB_RUBRIC`.
   - `KnowledgeDocument`: Ingests company documentation with title, content, categorization, target roles, and keyword tags.

2. **RAG Semantic Search & Retrieval Engine**:
   - Implemented `KnowledgeRAGEngine` in `backend/app/knowledge/rag_engine.py`.
   - Pre-seeded with industry-grade engineering standards (Stripe Idempotency, Netflix EVCache, Uber Resilience, Meta Sharding, Postgres Migrations).
   - Fast keyword and semantic overlap retrieval ranking documents by relevance score.

3. **Prompt Grounding & Verification Directives**:
   - `InterviewPromptBuilder` dynamically injects `[OFFICIAL COMPANY ENGINEERING STANDARD & RAG CONTEXT]` into LLM prompts on matching turns.
   - Directs the interviewer to verify candidate answers against official company guidelines.

4. **REST APIs & Frontend Management**:
   - `GET /api/knowledge/documents`, `POST /api/knowledge/ingest`, `POST /api/knowledge/search`.
   - Knowledge Base Drawer in `InterviewSetup.tsx` for inspecting and ingesting company documents.
   - Live RAG Context Badge in `VoiceRoom.tsx` HUD (`📚 RAG: Stripe Idempotency Standard`).

## Consequences
### Positive
- Ensures interview rigor matches the hiring organization's actual production standards.
- Allows hiring teams to easily add proprietary rubrics and question banks without code changes.
- Provides immediate candidate feedback grounded in company architecture.

### Tradeoffs
- Requires concise RAG snippet trimming to prevent token bloat during streaming LLM inference.
