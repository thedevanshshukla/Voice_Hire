from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.models.interview import InterviewConfig, InterviewStage, InterviewTopic
from app.core.logger import get_logger

logger = get_logger("interview.adaptive_engine")

class AnswerDepth(str, Enum):
    SHALLOW_OR_VAGUE = "shallow_or_vague"
    MODERATE = "moderate"
    STRONG_OR_COMPREHENSIVE = "strong_or_comprehensive"
    INCORRECT_OR_CONFUSED = "incorrect_or_confused"

class AdaptiveStrategy(str, Enum):
    PROBE_DEEPER = "probe_deeper"
    INCREASE_DIFFICULTY = "increase_difficulty"
    PIVOT_NEXT_TOPIC = "pivot_next_topic"
    PROVIDE_HINT = "provide_hint"

class AdaptiveAction(BaseModel):
    evaluated_depth: AnswerDepth
    strategy: AdaptiveStrategy
    target_topic: str
    difficulty_level: int = Field(default=2, ge=1, le=5)
    strategy_display: str
    guidance_directive: str

# Technical knowledge probes for shallow statements
SPECIALIZED_PROBES: Dict[str, Dict[str, str]] = {
    "redis": {
        "probe": "The candidate mentioned caching/Redis vaguely. Challenge them on: How do they prevent cache stampede (thundering herd), handle TTL expiry spikes, and ensure cache invalidation consistency with the primary DB?",
        "escalate": "The candidate understands Redis basics. Escalate complexity: Ask how they would architect a distributed multi-region write-through cache with sub-second replication and eviction under memory pressure."
    },
    "caching": {
        "probe": "The candidate mentioned caching vaguely. Challenge them on: How do they prevent cache stampede, handle TTL expiry spikes, and ensure cache invalidation consistency with the primary DB?",
        "escalate": "The candidate understands caching. Escalate: Ask about multi-region write-through cache replication and eviction policies."
    },
    "index": {
        "probe": "The candidate mentioned database indexing generally. Probe specifically on: What index structure was chosen (B-Tree vs Hash vs GIN), left-prefix matching, and how they evaluated selectivity via EXPLAIN ANALYZE.",
        "escalate": "The candidate understands indexes. Escalate complexity: Ask about PostgreSQL MVCC table bloat, serialization isolation level anomalies, and write-amplification tradeoffs of secondary indexes."
    },
    "lock": {
        "probe": "The candidate mentioned locking/concurrency vaguely. Probe specifically: Did they use optimistic locking with version columns, distributed Redis redlocks, or row-level SELECT FOR UPDATE? How are deadlocks avoided?",
        "escalate": "The candidate understands locks. Escalate: Ask about lock-free concurrency, memory barriers, atomic Compare-And-Swap (CAS), and CPU cache coherence (MESI)."
    },
    "kafka": {
        "probe": "The candidate mentioned message queues/Kafka. Probe specifically: How did they manage partition key distribution, consumer group rebalances, and achieve idempotent consumer processing?",
        "escalate": "The candidate understands Kafka. Escalate: Ask about out-of-order delivery recovery, transactional outbox patterns, and exactly-once processing (EOS) semantics."
    },
    "sharding": {
        "probe": "The candidate mentioned database sharding. Probe specifically: How did they choose the shard key, manage cross-shard queries/joins, and execute re-sharding without downtime?",
        "escalate": "The candidate understands sharding. Escalate: Ask about distributed two-phase commit (2PC) vs Saga orchestration and consensus algorithms like Raft for distributed metadata."
    }
}

DEPTH_INDICATORS = [
    "tradeoff", "trade-off", "because", "instead of", "consistency", "latency",
    "throughput", "invalidation", "stampede", "isolation", "deadlock", "cas",
    "rebalance", "partition", "idempotent", "index", "b-tree", "explain", "fallback",
    "replica", "vacuum", "bloat", "sharding", "saga", "optimistic", "pessimistic", "mutex"
]

class AdaptiveQuestionEngine:
    """
    Intelligent Adaptive Engine analyzing candidate response depth,
    generating dynamic follow-up probes, and rotating topics.
    """
    def __init__(self, config: Optional[InterviewConfig] = None):
        self.config = config or InterviewConfig()
        self.topics = self.config.topics or ["DBMS & SQL", "Operating Systems & Concurrency", "System Design & Architecture"]
        self.current_topic_index: int = 0
        self.current_difficulty: int = 2
        self.turns_in_current_topic: int = 0
        self.topic_stats: Dict[str, Dict[str, Any]] = {
            t: {"questions_asked": 0, "strong_answers": 0, "probes_triggered": 0}
            for t in self.topics
        }

    def get_active_topic(self) -> str:
        if not self.topics:
            return "General System Architecture"
        return self.topics[self.current_topic_index % len(self.topics)]

    def evaluate_depth(self, candidate_reply: str) -> AnswerDepth:
        text = candidate_reply.strip()
        words = text.split()
        word_count = len(words)
        lower_text = text.lower()

        # 1. Confused or non-answers
        if word_count < 4 or "i don't know" in lower_text or "not sure" in lower_text:
            return AnswerDepth.INCORRECT_OR_CONFUSED

        # 2. Count matched depth indicators
        matched_indicators = sum(1 for ind in DEPTH_INDICATORS if ind in lower_text)

        # 3. Check for superficial keyword drops
        vague_keywords = ["just used", "simply", "basic", "standard", "we used redis", "we used kafka", "we used docker", "we added an index"]
        is_vague_drop = any(vk in lower_text for vk in vague_keywords) and matched_indicators <= 1 and word_count < 18

        if is_vague_drop:
            return AnswerDepth.SHALLOW_OR_VAGUE

        if matched_indicators >= 2 and word_count >= 18:
            return AnswerDepth.STRONG_OR_COMPREHENSIVE
        elif matched_indicators >= 1 or word_count >= 12:
            return AnswerDepth.MODERATE
        else:
            return AnswerDepth.SHALLOW_OR_VAGUE

    def analyze_turn_and_plan(
        self,
        last_candidate_reply: str,
        current_stage: InterviewStage,
        last_interviewer_question: Optional[str] = None
    ) -> AdaptiveAction:
        active_topic = self.get_active_topic()
        depth = self.evaluate_depth(last_candidate_reply)
        self.turns_in_current_topic += 1
        
        if active_topic in self.topic_stats:
            self.topic_stats[active_topic]["questions_asked"] += 1

        lower_reply = last_candidate_reply.lower()

        # 1. SHALLOW ANSWER -> PROBE DEEPER
        if depth == AnswerDepth.SHALLOW_OR_VAGUE:
            strategy = AdaptiveStrategy.PROBE_DEEPER
            if active_topic in self.topic_stats:
                self.topic_stats[active_topic]["probes_triggered"] += 1
            
            # Find relevant domain probe
            probe_guidance = None
            for key, probe_data in SPECIALIZED_PROBES.items():
                if key in lower_reply:
                    probe_guidance = probe_data["probe"]
                    break
            
            if not probe_guidance:
                probe_guidance = f"The candidate gave a high-level answer regarding {active_topic}. Probe deeper on the underlying mechanism, failure modes, and concrete implementation choices."

            directive = (
                f"[ADAPTIVE DIRECTIVE: PROBE DEEPER]\n"
                f"Candidate's response was shallow or missing mechanism.\n"
                f"{probe_guidance}\n"
                f"Keep your follow-up concise, sharp, and focused on this exact point."
            )
            display = f"🔍 Probing Depth ({active_topic})"

        # 2. STRONG ANSWER -> INCREASE DIFFICULTY OR ROTATE TOPIC
        elif depth == AnswerDepth.STRONG_OR_COMPREHENSIVE:
            if active_topic in self.topic_stats:
                self.topic_stats[active_topic]["strong_answers"] += 1

            if self.turns_in_current_topic >= 2:
                # Rotate to next topic
                self.current_topic_index += 1
                self.turns_in_current_topic = 0
                new_topic = self.get_active_topic()
                strategy = AdaptiveStrategy.PIVOT_NEXT_TOPIC
                directive = (
                    f"[ADAPTIVE DIRECTIVE: PIVOT TO NEXT TOPIC]\n"
                    f"Candidate gave a comprehensive answer on {active_topic}.\n"
                    f"Acknowledge their strong insight in one short sentence, then smoothly transition to {new_topic}."
                )
                display = f"➡️ Mastered {active_topic} → Next: {new_topic}"
                active_topic = new_topic
            else:
                strategy = AdaptiveStrategy.INCREASE_DIFFICULTY
                self.current_difficulty = min(5, self.current_difficulty + 1)
                
                escalate_guidance = None
                for key, probe_data in SPECIALIZED_PROBES.items():
                    if key in lower_reply:
                        escalate_guidance = probe_data["escalate"]
                        break
                if not escalate_guidance:
                    escalate_guidance = f"Challenge the candidate with a higher-scale scenario in {active_topic} (e.g. high concurrency, split-brain recovery, or distributed state)."

                directive = (
                    f"[ADAPTIVE DIRECTIVE: ESCALATE DIFFICULTY]\n"
                    f"Candidate gave a strong fundamental answer on {active_topic}.\n"
                    f"{escalate_guidance}\n"
                    f"Ask a challenging senior-level follow-up question."
                )
                display = f"📈 Escalating Difficulty in {active_topic} (Lvl {self.current_difficulty})"

        # 3. CONFUSED / INCORRECT -> PROVIDE HINT
        elif depth == AnswerDepth.INCORRECT_OR_CONFUSED:
            strategy = AdaptiveStrategy.PROVIDE_HINT
            directive = (
                f"[ADAPTIVE DIRECTIVE: PROVIDE CONSTRUCTIVE HINT]\n"
                f"Candidate appears uncertain on {active_topic}.\n"
                f"Provide a brief 1-sentence architectural hint to guide their thinking, and invite them to reason through the problem with you."
            )
            display = f"💡 Guiding with Hint ({active_topic})"

        # 4. MODERATE ANSWER -> DEEPEN TOPIC
        else:
            strategy = AdaptiveStrategy.PROBE_DEEPER
            directive = (
                f"[ADAPTIVE DIRECTIVE: EXPLORE TRADEOFFS]\n"
                f"Candidate understands basic concepts of {active_topic}.\n"
                f"Ask them to compare trade-offs of this approach vs an alternative solution."
            )
            display = f"⚖️ Exploring Trade-offs ({active_topic})"

        logger.info("Adaptive Action Planned", extra={
            "depth": depth.value,
            "strategy": strategy.value,
            "topic": active_topic,
            "difficulty": self.current_difficulty
        })

        return AdaptiveAction(
            evaluated_depth=depth,
            strategy=strategy,
            target_topic=active_topic,
            difficulty_level=self.current_difficulty,
            strategy_display=display,
            guidance_directive=directive
        )
