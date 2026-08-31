import re
from typing import List, Optional, Dict, Any
from app.models.knowledge import KnowledgeDocument, KnowledgeCategory, KnowledgeSearchResult
from app.core.logger import get_logger

logger = get_logger("knowledge.rag_engine")

INITIAL_COMPANY_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "id": "doc-stripe-idempotency",
        "title": "Stripe Idempotency & Distributed Lock Standard",
        "category": KnowledgeCategory.COMPANY_STANDARDS,
        "tags": ["idempotency", "api", "redis", "lock", "stripe", "payments", "retry", "concurrency"],
        "role_target": "Backend Engineer",
        "content": (
            "When designing idempotent APIs, clients must provide a unique Idempotency-Key in the request header. "
            "The server acquires a distributed lock in Redis with a 30-second TTL. If the request was previously processed, "
            "the server returns the cached response payload immediately. If processing is underway, it returns 409 Conflict. "
            "Critical requirement: Ensure atomic database writes alongside idempotency key state to prevent duplicate side-effects."
        )
    },
    {
        "id": "doc-netflix-caching",
        "title": "Netflix High-Throughput Tier-1 Caching & Stampede Prevention",
        "category": KnowledgeCategory.ARCHITECTURE_PATTERNS,
        "tags": ["caching", "redis", "memcached", "evcache", "stampede", "netflix", "ttl", "invalidation"],
        "role_target": "Backend Engineer",
        "content": (
            "For tier-1 distributed caching, use consistent hashing across nodes with probabilistic early expiration (XFetch algorithm) "
            "to prevent cache stampede (thundering herd). Maintain an in-memory L1 cache with a distributed L2 cache, backing all cache "
            "misses with circuit-breaker protected database reads. Never rely on unbounded TTLs."
        )
    },
    {
        "id": "doc-uber-resilience",
        "title": "Uber Microservice Circuit Breaker & Fallback Standard",
        "category": KnowledgeCategory.COMPANY_STANDARDS,
        "tags": ["microservices", "resilience", "circuit breaker", "fallback", "uber", "latency", "grpc"],
        "role_target": "Distributed Systems Architect",
        "content": (
            "Every inter-service call must configure a circuit breaker with 3 states: Closed, Open, Half-Open. "
            "If error rate exceeds 50% over a 10s rolling window, immediately trip to Open and return a degraded fallback payload "
            "rather than propagating latency storms upstream. Include exponential backoff jitter on all retries."
        )
    },
    {
        "id": "doc-meta-sharding",
        "title": "Meta Database Sharding & Partition Key Selection Guidelines",
        "category": KnowledgeCategory.ARCHITECTURE_PATTERNS,
        "tags": ["sharding", "database", "sql", "partition", "mysql", "meta", "scaling", "joins"],
        "role_target": "Distributed Systems Architect",
        "content": (
            "Shard databases using high-cardinality immutable entity keys (e.g. user_id). Never execute cross-shard distributed joins; "
            "denormalize secondary lookup tables asynchronously using Change Data Capture (CDC) streams. "
            "Resharding must use virtual bucket mappings to avoid physical re-partitioning downtime."
        )
    },
    {
        "id": "doc-postgres-migrations",
        "title": "PostgreSQL Zero-Downtime Migrations & MVCC Maintenance",
        "category": KnowledgeCategory.COMPANY_STANDARDS,
        "tags": ["postgres", "mvcc", "indexes", "migration", "lock", "vacuum", "dbms", "selectivity"],
        "role_target": "Backend Engineer",
        "content": (
            "Always create indexes using CREATE INDEX CONCURRENTLY to avoid blocking table writes. "
            "When adding columns with default values, use Postgres 11+ metadata-only defaults to eliminate table rewrites. "
            "Tune autovacuum settings aggressively on high-write tables to eliminate MVCC bloat and transaction wraparound."
        )
    }
]

class KnowledgeRAGEngine:
    """
    Retrieval-Augmented Generation engine for indexing and querying company engineering standards,
    custom question banks, and evaluation rubrics during live interviews.
    """

    def __init__(self):
        self.documents: Dict[str, KnowledgeDocument] = {}
        self._seed_default_documents()

    def _seed_default_documents(self):
        for item in INITIAL_COMPANY_KNOWLEDGE:
            doc = KnowledgeDocument(
                id=item["id"],
                title=item["title"],
                category=item["category"],
                tags=item["tags"],
                role_target=item.get("role_target"),
                content=item["content"]
            )
            self.documents[doc.id] = doc

    def ingest_document(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        self.documents[doc.id] = doc
        logger.info("Ingested Knowledge Document", extra={"doc_id": doc.id, "title": doc.title})
        return doc

    def get_all_documents(self) -> List[KnowledgeDocument]:
        return list(self.documents.values())

    def search(
        self,
        query: str,
        role_target: Optional[str] = None,
        top_k: int = 2
    ) -> List[KnowledgeSearchResult]:
        if not query.strip():
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        results: List[KnowledgeSearchResult] = []

        for doc in self.documents.values():
            doc_text = (doc.title + " " + doc.content + " " + " ".join(doc.tags)).lower()
            doc_tokens = set(re.findall(r"\w+", doc_text))

            # Keyword overlap score
            overlap = query_tokens.intersection(doc_tokens)
            if not overlap:
                continue

            score = len(overlap) / float(len(query_tokens) + 2)

            # Role target boost
            if role_target and doc.role_target and role_target.lower() in doc.role_target.lower():
                score += 0.2

            # Tag exact match boost
            for tag in doc.tags:
                if tag.lower() in query.lower():
                    score += 0.3

            if score > 0.15:
                # Extract matching snippet
                snippet = doc.content[:240] + ("..." if len(doc.content) > 240 else "")
                results.append(KnowledgeSearchResult(
                    doc_id=doc.id,
                    title=doc.title,
                    category=doc.category,
                    matched_snippet=snippet,
                    relevance_score=round(min(1.0, score), 2)
                ))

        # Sort by relevance score descending
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]
