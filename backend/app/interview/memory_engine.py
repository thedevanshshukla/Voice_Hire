import re
from typing import List, Optional, Dict, Any
from app.models.interview import (
    ShortTermMemory, ClaimEntity, ContradictionItem, CandidateProfile,
    InterviewSession, InterviewStage
)
from app.core.logger import get_logger

logger = get_logger("interview.memory_engine")

TECH_EXTRACTORS = [
    {"name": "PostgreSQL", "pattern": r"(postgres|postgresql)"},
    {"name": "MySQL", "pattern": r"(mysql|mariadb)"},
    {"name": "MongoDB", "pattern": r"(mongodb|mongo)"},
    {"name": "Redis", "pattern": r"(redis|memcached)"},
    {"name": "Kafka", "pattern": r"(kafka|rabbitmq|sqs)"},
    {"name": "Optimistic Locking", "pattern": r"(optimistic lock|version column|versioning)"},
    {"name": "Pessimistic Locking", "pattern": r"(pessimistic lock|select for update|row lock)"},
    {"name": "gRPC", "pattern": r"(grpc|protobuf)"},
    {"name": "Kubernetes", "pattern": r"(kubernetes|k8s|docker)"}
]

# Contradiction rules between technologies/claims
CONTRADICTION_RULES = [
    {
        "tech_a": "PostgreSQL",
        "contradict_patterns": [r"never used sql", r"never used relational", r"pure nosql.*no relational", r"didn't use postgres"],
        "explanation": "Contradicted earlier claim of using PostgreSQL / relational databases."
    },
    {
        "tech_a": "Kafka",
        "contradict_patterns": [r"never used kafka", r"didn't use message queue", r"no event streaming", r"purely synchronous.*no queue"],
        "explanation": "Contradicted earlier claim of using Kafka / message queues."
    },
    {
        "tech_a": "Optimistic Locking",
        "contradict_patterns": [r"never used optimistic", r"always used pessimistic row locks everywhere"],
        "explanation": "Contradicted earlier concurrency strategy regarding optimistic locking."
    },
    {
        "tech_a": "Redis",
        "contradict_patterns": [r"never used caching", r"no cache layer", r"didn't use redis"],
        "explanation": "Contradicted earlier caching architecture claim."
    }
]

class InterviewMemoryEngine:
    """
    Manages short-term working memory within a single interview session:
    extracts candidate technical claims, synthesizes cross-turn callbacks,
    and flags logical contradictions.
    """

    def __init__(self, initial_memory: Optional[ShortTermMemory] = None):
        self.memory = initial_memory or ShortTermMemory()

    def process_candidate_turn(
        self,
        candidate_text: str,
        turn_index: int,
        stage: InterviewStage
    ) -> List[ContradictionItem]:
        text = candidate_text.strip()
        lower = text.lower()
        new_contradictions: List[ContradictionItem] = []

        # 1. Check for contradictions against earlier claims
        for claim in self.memory.claims:
            for rule in CONTRADICTION_RULES:
                if rule["tech_a"].lower() in claim.statement.lower():
                    for cp in rule["contradict_patterns"]:
                        if re.search(cp, lower):
                            contra = ContradictionItem(
                                earlier_claim=claim.statement,
                                current_claim=text[:140] + ("..." if len(text) > 140 else ""),
                                topic=claim.topic,
                                explanation=rule["explanation"],
                                detected_at_turn=turn_index
                            )
                            self.memory.contradictions.append(contra)
                            new_contradictions.append(contra)
                            logger.warning("Contradiction Detected", extra={
                                "earlier": claim.statement,
                                "current": text[:100],
                                "explanation": rule["explanation"]
                            })

        # 2. Extract new claims & technologies mentioned
        for extractor in TECH_EXTRACTORS:
            if re.search(extractor["pattern"], lower):
                tech_name = extractor["name"]
                if tech_name not in self.memory.mentioned_technologies:
                    self.memory.mentioned_technologies.append(tech_name)

                # Extract matching sentence as claim
                sentences = re.split(r"[.!?]", text)
                matched_sentence = next((s.strip() for s in sentences if re.search(extractor["pattern"], s.lower())), text[:120])

                claim = ClaimEntity(
                    topic=tech_name,
                    statement=matched_sentence,
                    turn_index=turn_index,
                    stage=stage.value if hasattr(stage, "value") else str(stage)
                )
                self.memory.claims.append(claim)

        return new_contradictions

    def generate_cross_turn_reference(self, current_topic: str) -> Optional[str]:
        """
        Generates a natural conversational reference to an earlier claim matching the active topic.
        """
        lower_topic = current_topic.lower()
        relevant_claims = [
            c for c in self.memory.claims
            if c.topic.lower() in lower_topic or any(w in c.statement.lower() for w in lower_topic.split())
        ]

        if not relevant_claims:
            return None

        claim = relevant_claims[0]
        callback = f"Earlier in the {claim.stage.replace('_', ' ')} stage, you mentioned: \"{claim.statement}\"."
        
        if callback not in self.memory.cross_turn_callbacks_used:
            self.memory.cross_turn_callbacks_used.append(callback)
            return (
                f"[CROSS-TURN MEMORY CALLBACK DIRECTIVE]:\n"
                f"Candidate previously stated: \"{claim.statement}\" ({claim.stage} stage).\n"
                f"Weave a natural reference to this earlier choice into your next question to test architectural consistency."
            )
        return None

# ==========================================
# Long-Term Candidate Profile Repository
# ==========================================

class CandidateProfileRepository:
    """
    In-memory / persistent repository tracking candidate progression across multiple interview rounds.
    """
    _profiles: Dict[str, CandidateProfile] = {}

    @classmethod
    def get_profile(cls, candidate_id: str, candidate_name: str = "Candidate") -> CandidateProfile:
        if candidate_id not in cls._profiles:
            cls._profiles[candidate_id] = CandidateProfile(
                candidate_id=candidate_id,
                candidate_name=candidate_name
            )
        return cls._profiles[candidate_id]

    @classmethod
    def record_session_completion(cls, session: InterviewSession) -> CandidateProfile:
        profile = cls.get_profile(session.candidate_id, session.candidate_name)
        if session.session_id not in profile.past_session_ids:
            profile.past_session_ids.append(session.session_id)

        round_num = len(profile.round_progression) + 1
        score = session.scorecard.overall_score if session.scorecard else 0.0

        profile.round_progression.append({
            "round": round_num,
            "session_id": session.session_id,
            "role": session.config.role.value,
            "level": session.config.experience_level.value,
            "overall_score": score,
            "verdict": session.scorecard.summary_verdict if session.scorecard else "Completed"
        })

        if session.scorecard:
            profile.cumulative_strengths.extend(session.scorecard.top_strengths)
            profile.cumulative_weaknesses.extend(session.scorecard.areas_for_improvement)
            # Deduplicate
            profile.cumulative_strengths = list(dict.fromkeys(profile.cumulative_strengths))
            profile.cumulative_weaknesses = list(dict.fromkeys(profile.cumulative_weaknesses))

        cls._profiles[profile.candidate_id] = profile
        return profile
