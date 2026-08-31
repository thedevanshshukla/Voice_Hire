from typing import List, Dict, Optional, Any
from app.models.interview import TurnEvaluation, SessionScorecard, InterviewStage, InterviewConfig
from app.core.logger import get_logger

logger = get_logger("interview.evaluation_engine")

PRACTICAL_KEYWORDS = [
    "production", "outage", "debugged", "monitoring", "prometheus", "grafana",
    "incident", "latency spike", "alert", "runbook", "canary", "profiling",
    "benchmark", "fallback", "circuit breaker", "retry storm", "deadlock in prod"
]

TRADEOFF_KEYWORDS = [
    "tradeoff", "trade-off", "compromise", "instead of", "downside", "drawback",
    "overhead", "amplification", "consistency vs availability", "cap theorem",
    "cpu vs memory", "cost vs latency", "eventual consistency"
]

MECHANISM_KEYWORDS = [
    "b-tree", "hash table", "lock-free", "cas", "mutex", "optimistic", "pessimistic",
    "vacuum", "mvcc", "wal", "write-ahead log", "leader election", "raft", "paxos",
    "index scan", "explain analyze", "gc pause", "memory barrier", "consistent hashing"
]

class AnswerEvaluator:
    """
    Evaluates candidate technical responses across 5 core dimensions:
    1. Correctness
    2. Depth & Mechanics
    3. Communication Clarity
    4. Trade-off Awareness
    5. Practical Experience vs Theory
    """
    
    @staticmethod
    def evaluate_turn(
        candidate_reply: str,
        topic: str = "General Engineering",
        stage: InterviewStage = InterviewStage.CORE_CONCEPTS
    ) -> TurnEvaluation:
        text = candidate_reply.strip()
        lower = text.lower()
        words = text.split()
        word_count = len(words)

        # Base scoring
        correctness = 3.0
        depth = 3.0
        clarity = 3.5
        tradeoffs = 2.5
        practical = 2.5
        strengths: List[str] = []
        gaps: List[str] = []

        # 1. Evaluate Confusion / Refusal
        if word_count < 4 or "i don't know" in lower or "not sure" in lower:
            return TurnEvaluation(
                overall_score=1.5,
                correctness=1.5,
                depth=1.0,
                communication_clarity=3.0,
                tradeoff_awareness=1.0,
                practical_vs_theory=1.0,
                strengths=[],
                gaps=["Did not provide technical explanation for the question."],
                feedback="Candidate was unable to answer or lacked familiarity with this domain."
            )

        # 2. Evaluate Depth & Mechanics
        matched_mechanisms = [m for m in MECHANISM_KEYWORDS if m in lower]
        if len(matched_mechanisms) >= 2:
            depth = 4.5
            strengths.append(f"Clear grasp of underlying mechanisms ({', '.join(matched_mechanisms[:2])}).")
        elif len(matched_mechanisms) == 1:
            depth = 3.8
            strengths.append(f"Mentioned core mechanism: {matched_mechanisms[0]}.")
        elif word_count < 15:
            depth = 2.0
            gaps.append("Answer was superficial; omitted underlying architectural mechanisms.")
        else:
            depth = 3.0

        # 3. Evaluate Trade-off Awareness
        matched_tradeoffs = [t for t in TRADEOFF_KEYWORDS if t in lower]
        if len(matched_tradeoffs) >= 2:
            tradeoffs = 4.8
            strengths.append("Exceptional trade-off reasoning and architectural evaluation.")
        elif len(matched_tradeoffs) == 1:
            tradeoffs = 4.0
            strengths.append("Demonstrated awareness of design trade-offs.")
        else:
            tradeoffs = 2.5
            gaps.append("Did not explicitly weigh downsides or trade-offs of the chosen approach.")

        # 4. Evaluate Practical Experience vs Theory
        matched_practical = [p for p in PRACTICAL_KEYWORDS if p in lower]
        if len(matched_practical) >= 1:
            practical = 4.5
            strengths.append(f"Cited real-world production experience ({', '.join(matched_practical[:2])}).")
        elif word_count >= 30 and depth >= 3.5:
            practical = 3.5
        else:
            practical = 2.5

        # 5. Evaluate Clarity
        if 15 <= word_count <= 80:
            clarity = 4.5
        elif word_count > 120:
            clarity = 3.0
            gaps.append("Response was slightly verbose / unstructured.")
        else:
            clarity = 3.5

        # 6. Evaluate Correctness
        if "wrong" in lower or "always safe" in lower or (depth <= 2.0 and word_count < 10):
            correctness = 2.5
        elif depth >= 4.0 and tradeoffs >= 4.0:
            correctness = 4.8
        elif depth >= 3.5:
            correctness = 4.0
        else:
            correctness = 3.2

        # Compute weighted overall score
        # Correctness: 25%, Depth: 25%, Clarity: 15%, Tradeoffs: 20%, Practical: 15%
        overall = (
            (correctness * 0.25) +
            (depth * 0.25) +
            (clarity * 0.15) +
            (tradeoffs * 0.20) +
            (practical * 0.15)
        )
        overall_score = round(min(5.0, max(1.0, overall)), 2)

        if not strengths:
            strengths.append("Provided basic relevant domain answer.")
        if not gaps and overall_score < 4.5:
            gaps.append("Could expand further on failure recovery and edge cases.")

        feedback = (
            f"Strong answer on {topic}" if overall_score >= 4.0
            else f"Adequate explanation of {topic}, but could deepen trade-offs and edge-case mechanics."
        )

        logger.info("Evaluated candidate turn", extra={
            "overall": overall_score,
            "correctness": correctness,
            "depth": depth,
            "tradeoffs": tradeoffs,
            "practical": practical
        })

        return TurnEvaluation(
            overall_score=overall_score,
            correctness=round(correctness, 1),
            depth_and_mechanics=round(depth, 1),
            communication_clarity=round(clarity, 1),
            tradeoff_awareness=round(tradeoffs, 1),
            practical_vs_theory=round(practical, 1),
            strengths=strengths,
            gaps=gaps,
            feedback=feedback
        )

    @staticmethod
    def aggregate_scorecard(evaluations: List[TurnEvaluation]) -> SessionScorecard:
        if not evaluations:
            return SessionScorecard()

        count = len(evaluations)
        avg_overall = sum(e.overall_score for e in evaluations) / count
        avg_correct = sum(e.correctness for e in evaluations) / count
        avg_depth = sum(e.depth_and_mechanics for e in evaluations) / count
        avg_clarity = sum(e.communication_clarity for e in evaluations) / count
        avg_tradeoffs = sum(e.tradeoff_awareness for e in evaluations) / count
        avg_practical = sum(e.practical_vs_theory for e in evaluations) / count

        all_strengths = []
        all_gaps = []
        for e in evaluations:
            all_strengths.extend(e.strengths)
            all_gaps.extend(e.gaps)

        # Deduplicate top strengths & gaps
        unique_strengths = list(dict.fromkeys(all_strengths))[:4]
        unique_gaps = list(dict.fromkeys(all_gaps))[:4]

        passed = avg_overall >= 3.5
        if avg_overall >= 4.3:
            verdict = "Strong Hire (Exceeds Bar with Deep Mechanics & Trade-offs)"
        elif avg_overall >= 3.5:
            verdict = "Hire (Meets Technical Bar with Solid Fundamentals)"
        elif avg_overall >= 2.8:
            verdict = "Borderline / Lean No Hire (Needs Deeper Production Mechanics)"
        else:
            verdict = "No Hire (Superficial Depth & Missing Fundamentals)"

        return SessionScorecard(
            overall_score=round(avg_overall, 2),
            avg_correctness=round(avg_correct, 2),
            avg_depth=round(avg_depth, 2),
            avg_clarity=round(avg_clarity, 2),
            avg_tradeoffs=round(avg_tradeoffs, 2),
            avg_practical=round(avg_practical, 2),
            total_evaluated_turns=count,
            passed_recommendation=passed,
            summary_verdict=verdict,
            top_strengths=unique_strengths,
            areas_for_improvement=unique_gaps
        )
