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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    turn_count: int = 0
    transcripts: List[TranscriptEntry] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
