from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class InterviewRole(str, Enum):
    BACKEND = "Backend Engineer"
    FRONTEND = "Frontend Engineer"
    FULLSTACK = "Fullstack Engineer"
    DEVOPS = "DevOps / SRE Engineer"
    SYSTEM_DESIGN = "Distributed Systems Architect"

class ExperienceLevel(str, Enum):
    JUNIOR = "SDE-1 (0-2 years)"
    MID = "SDE-2 (2-5 years)"
    SENIOR = "Senior / SDE-3 (5-8 years)"
    STAFF = "Staff / Principal (8+ years)"

class InterviewLanguage(str, Enum):
    ENGLISH = "English"
    HINDI = "Hindi"

class InterviewTopic(str, Enum):
    DBMS = "DBMS & SQL"
    OS = "Operating Systems & Concurrency"
    NETWORKING = "Networking & Protocols"
    SYSTEM_DESIGN = "System Design & Architecture"
    REDIS_CACHING = "Caching & Redis"
    DISTRIBUTED_SYSTEMS = "Distributed Systems"
    APIS = "REST & GraphQL API Design"
    KAFKA_QUEUES = "Message Queues & Event Streaming"

class InterviewStage(str, Enum):
    GREETING = "greeting"
    RESUME_DEEP_DIVE = "resume_deep_dive"
    CORE_CONCEPTS = "core_concepts"
    SYSTEM_DESIGN = "system_design"
    CANDIDATE_QUESTIONS = "candidate_questions"
    WRAP_UP = "wrap_up"

class TurnEvaluation(BaseModel):
    overall_score: float = Field(..., ge=1.0, le=5.0, description="Overall weighted turn score (1-5)")
    correctness: float = Field(default=3.0, ge=1.0, le=5.0, description="Technical accuracy and correctness")
    depth_and_mechanics: float = Field(default=3.0, ge=1.0, le=5.0, description="Depth of underlying mechanisms")
    communication_clarity: float = Field(default=3.0, ge=1.0, le=5.0, description="Clarity and structured thought")
    tradeoff_awareness: float = Field(default=3.0, ge=1.0, le=5.0, description="Explicit trade-off reasoning")
    practical_vs_theory: float = Field(default=3.0, ge=1.0, le=5.0, description="Real-world production experience vs theory")
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    feedback: str = ""

class SessionScorecard(BaseModel):
    overall_score: float = Field(default=0.0, description="Average composite score across all evaluated turns")
    avg_correctness: float = 0.0
    avg_depth: float = 0.0
    avg_clarity: float = 0.0
    avg_tradeoffs: float = 0.0
    avg_practical: float = 0.0
    total_evaluated_turns: int = 0
    passed_recommendation: bool = False
    summary_verdict: str = "Evaluation pending"
    top_strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)

class EvidenceSnippet(BaseModel):
    quote: str = Field(..., description="Verbatim quote from candidate transcript")
    topic: str = "General"
    stage: str = "core_concepts"
    dimension: str = "Technical Depth"
    rationale: str = ""

class RedFlagItem(BaseModel):
    category: str = Field(..., description="e.g. UNSUPPORTED_CLAIM, FATAL_MISCONCEPTION, FAILURE_IGNORANCE")
    quote: str = Field(..., description="Verbatim quote triggering the red flag")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    explanation: str = ""

class EvidenceEvaluationReport(BaseModel):
    session_id: str
    candidate_name: str
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in evaluation based on sample depth")
    recommendation: str = Field(default="HIRE", description="STRONG_HIRE, HIRE, BORDERLINE, NO_HIRE")
    recommendation_reasoning: str = ""
    key_strengths_with_evidence: List[EvidenceSnippet] = Field(default_factory=list)
    key_weaknesses_with_evidence: List[EvidenceSnippet] = Field(default_factory=list)
    red_flags: List[RedFlagItem] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class InterviewConfig(BaseModel):
    role: InterviewRole = InterviewRole.BACKEND
    experience_level: ExperienceLevel = ExperienceLevel.MID
    job_description: Optional[str] = Field(None, description="Optional raw text of the target job description")
    topics: List[str] = Field(
        default_factory=lambda: ["DBMS & SQL", "Operating Systems & Concurrency", "System Design & Architecture"],
        description="Selected technical topics to evaluate"
    )
    duration_minutes: int = Field(default=30, ge=10, le=60, description="Target interview duration in minutes")
    language: InterviewLanguage = InterviewLanguage.ENGLISH

class TranscriptEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage: InterviewStage = InterviewStage.GREETING
    role: str # "candidate" or "interviewer"
    text: str
    evaluated_depth: Optional[str] = Field(None, description="Evaluated depth of candidate response")
    adaptive_strategy: Optional[str] = Field(None, description="Applied adaptive questioning strategy")
    evaluation: Optional[TurnEvaluation] = Field(None, description="Detailed multi-dimensional turn evaluation")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: Optional[Dict[str, Any]] = None
    was_interrupted: bool = False

class SessionStatus(str, Enum):
    CONFIGURED = "configured"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"

class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"session-{uuid.uuid4().hex[:8]}")
    candidate_id: str = Field(default_factory=lambda: f"cand-{uuid.uuid4().hex[:6]}")
    candidate_name: str = "Candidate"
    config: InterviewConfig = Field(default_factory=InterviewConfig)
    status: SessionStatus = SessionStatus.CONFIGURED
    current_stage: InterviewStage = InterviewStage.GREETING
    stage_turn_counts: Dict[str, int] = Field(default_factory=lambda: {
        "greeting": 0,
        "resume_deep_dive": 0,
        "core_concepts": 0,
        "system_design": 0,
        "candidate_questions": 0,
        "wrap_up": 0
    })
    topic_coverage: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Questions asked & depth scores per topic")
    scorecard: Optional[SessionScorecard] = Field(default_factory=SessionScorecard, description="Cumulative multi-dimensional scorecard")
    evidence_report: Optional[EvidenceEvaluationReport] = Field(None, description="Evidence-backed hiring audit report")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    turn_count: int = 0
    transcripts: List[TranscriptEntry] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
