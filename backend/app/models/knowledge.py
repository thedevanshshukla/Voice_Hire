from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

class KnowledgeCategory(str, Enum):
    COMPANY_STANDARDS = "company_standards"
    QUESTION_BANK = "question_bank"
    ARCHITECTURE_PATTERNS = "architecture_patterns"
    JOB_RUBRIC = "job_rubric"

class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4().hex[:8]}")
    title: str = Field(..., description="Document or rubric title")
    category: KnowledgeCategory = KnowledgeCategory.COMPANY_STANDARDS
    content: str = Field(..., description="Full text content of the engineering standard / rubric")
    tags: List[str] = Field(default_factory=list, description="Keywords for indexing and retrieval")
    role_target: Optional[str] = Field(None, description="Optional target role (e.g. Backend Engineer)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class KnowledgeSearchResult(BaseModel):
    doc_id: str
    title: str
    category: KnowledgeCategory
    matched_snippet: str
    relevance_score: float
