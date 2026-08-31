import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import InterviewConfig, InterviewRole, ExperienceLevel, InterviewStage
from app.models.knowledge import KnowledgeDocument, KnowledgeCategory
from app.knowledge.rag_engine import KnowledgeRAGEngine
from app.interview.prompt_builder import InterviewPromptBuilder

def test_rag_engine_preseeded_documents_and_search():
    engine = KnowledgeRAGEngine()
    docs = engine.get_all_documents()
    assert len(docs) >= 5

    # 1. Query for idempotency
    res_idempotency = engine.search("How do we handle idempotency keys and distributed redis locks?", role_target="Backend Engineer")
    assert len(res_idempotency) >= 1
    assert "Stripe" in res_idempotency[0].title
    assert "Idempotency-Key" in res_idempotency[0].matched_snippet

    # 2. Query for cache stampede
    res_cache = engine.search("Preventing cache stampede and thundering herd with TTL", top_k=1)
    assert len(res_cache) >= 1
    assert "Netflix" in res_cache[0].title or "Caching" in res_cache[0].title

def test_rag_engine_custom_document_ingestion():
    engine = KnowledgeRAGEngine()
    custom_doc = KnowledgeDocument(
        title="Acme Corp: Zero-Trust Microservice Auth & Envoy Mesh",
        category=KnowledgeCategory.COMPANY_STANDARDS,
        tags=["auth", "envoy", "jwt", "mTLS", "security"],
        role_target="DevOps / SRE Engineer",
        content="All service-to-service communication must enforce mTLS via Envoy sidecars with SPIFFE/SPIRE x509 SVID identity tokens."
    )
    engine.ingest_document(custom_doc)

    res = engine.search("Envoy mTLS authentication standard", role_target="DevOps / SRE Engineer")
    assert len(res) >= 1
    assert "Acme Corp" in res[0].title
    assert "SPIFFE" in res[0].matched_snippet

def test_prompt_builder_injects_rag_context():
    config = InterviewConfig(role=InterviewRole.BACKEND, experience_level=ExperienceLevel.SENIOR)
    rag_snippet = "Stripe Idempotency Standard: Client must pass Idempotency-Key header; acquire Redis lock with 30s TTL."
    
    prompt = InterviewPromptBuilder.build_system_prompt(
        config=config,
        candidate_name="Alex",
        stage=InterviewStage.SYSTEM_DESIGN,
        rag_context=rag_snippet
    )
    assert "[OFFICIAL COMPANY ENGINEERING STANDARD & RAG CONTEXT]" in prompt
    assert "Stripe Idempotency Standard" in prompt

@pytest.mark.asyncio
async def test_api_knowledge_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. List docs
        list_resp = await ac.get("/api/knowledge/documents")
        assert list_resp.status_code == 200
        docs = list_resp.json()
        assert len(docs) >= 5

        # 2. Ingest custom rubric
        ingest_resp = await ac.post("/api/knowledge/ingest", json={
            "title": "Custom L6 Distributed Systems Rubric",
            "category": "job_rubric",
            "tags": ["rubric", "staff", "distributed"],
            "content": "Candidate must articulate consensus algorithm tradeoffs (Raft vs Paxos) under network partitions."
        })
        assert ingest_resp.status_code == 200
        assert ingest_resp.json()["title"] == "Custom L6 Distributed Systems Rubric"

        # 3. Search knowledge base
        search_resp = await ac.post("/api/knowledge/search", json={
            "query": "Raft consensus under partition",
            "top_k": 2
        })
        assert search_resp.status_code == 200
        matches = search_resp.json()
        assert len(matches) >= 1
