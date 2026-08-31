import re
from typing import List, Optional, Dict, Any
from app.models.interview import (
    InterviewSession, TranscriptEntry, EvidenceSnippet, RedFlagItem,
    EvidenceEvaluationReport, SessionScorecard, InterviewStage
)
from app.core.logger import get_logger

logger = get_logger("interview.evidence_engine")

# Red flag detection patterns
RED_FLAG_PATTERNS = [
    {
        "category": "FATAL_MISCONCEPTION",
        "pattern": r"(zero[- ]latency|no latency|100% (acid|consistent).*no tradeoff|acid across microservices|never drops|never fails)",
        "severity": "HIGH",
        "explanation": "Claimed zero-latency or impossible consistency guarantees without trade-offs in distributed systems."
    },
    {
        "category": "FAILURE_IGNORANCE",
        "pattern": r"(didn't need retries|network is always reliable|redis never crashes|database never has deadlocks)",
        "severity": "CRITICAL",
        "explanation": "Ignored distributed failure modes and network partitions (CAP theorem violation)."
    },
    {
        "category": "SUPERFICIAL_BUZZWORD",
        "pattern": r"(just used blockchain|simply used ai to solve it|magic|just works)",
        "severity": "LOW",
        "explanation": "Relied on superficial buzzwords rather than concrete architectural mechanisms."
    }
]

class EvidenceEvaluator:
    """
    Synthesizes evidence-based evaluation reports backed by verbatim quotes from candidate transcripts,
    identifies technical red flags, and calculates hiring confidence.
    """

    @staticmethod
    def extract_evidence_report(session: InterviewSession) -> EvidenceEvaluationReport:
        candidate_turns = [
            t for t in session.transcripts
            if t.role == "candidate" and len(t.text.strip()) > 0
        ]

        strengths_with_evidence: List[EvidenceSnippet] = []
        weaknesses_with_evidence: List[EvidenceSnippet] = []
        red_flags: List[RedFlagItem] = []

        # 1. Scan candidate turns for quote evidence & red flags
        claimed_expertise = False
        expert_topic = ""

        for turn in candidate_turns:
            text = turn.text.strip()
            lower = text.lower()

            # Check claim of expertise
            if any(exp in lower for exp in ["expert in", "led the entire", "built from scratch single-handedly", "master of"]):
                claimed_expertise = True
                expert_topic = text

            # Check red flag regex patterns
            for rfp in RED_FLAG_PATTERNS:
                if re.search(rfp["pattern"], lower):
                    red_flags.append(RedFlagItem(
                        category=rfp["category"],
                        quote=text[:160] + ("..." if len(text) > 160 else ""),
                        severity=rfp["severity"],
                        explanation=rfp["explanation"]
                    ))

            # Turn-level evidence extraction
            ev = turn.evaluation
            if ev:
                if ev.overall_score >= 4.0:
                    # High-scoring strength quote
                    rationale = ev.strengths[0] if ev.strengths else "Demonstrated deep architectural grasp."
                    strengths_with_evidence.append(EvidenceSnippet(
                        quote=text[:180] + ("..." if len(text) > 180 else ""),
                        topic=session.config.role.value,
                        stage=turn.stage.value if hasattr(turn.stage, "value") else str(turn.stage),
                        dimension="Depth & Trade-offs",
                        rationale=rationale
                    ))
                elif ev.overall_score <= 2.5:
                    # Low-scoring gap quote
                    rationale = ev.gaps[0] if ev.gaps else "Superficial answer lacking concrete mechanics."
                    weaknesses_with_evidence.append(EvidenceSnippet(
                        quote=text[:180] + ("..." if len(text) > 180 else ""),
                        topic=session.config.role.value,
                        stage=turn.stage.value if hasattr(turn.stage, "value") else str(turn.stage),
                        dimension="Core Fundamentals",
                        rationale=rationale
                    ))

                    # If candidate previously claimed expertise but failed this turn -> Flag UNSUPPORTED_CLAIM
                    if claimed_expertise:
                        red_flags.append(RedFlagItem(
                            category="UNSUPPORTED_CLAIM",
                            quote=text[:160] + "...",
                            severity="HIGH",
                            explanation="Candidate claimed senior-level expertise earlier but failed basic follow-up mechanics."
                        ))
                        claimed_expertise = False # Flag once

        # Deduplicate and limit evidence snippets
        unique_strengths = strengths_with_evidence[:4]
        unique_weaknesses = weaknesses_with_evidence[:4]

        # 2. Compute Confidence Score (0.0 to 1.0)
        total_evals = len([t for t in candidate_turns if t.evaluation is not None])
        confidence = min(1.0, max(0.4, round(0.4 + (total_evals * 0.15), 2)))

        # 3. Formulate Hiring Recommendation with Executive Reasoning
        scorecard = session.scorecard or SessionScorecard()
        overall = scorecard.overall_score if scorecard.overall_score > 0 else (
            sum(t.evaluation.overall_score for t in candidate_turns if t.evaluation) / max(1, total_evals)
        )

        has_critical_red_flags = any(rf.severity in ["HIGH", "CRITICAL"] for rf in red_flags)

        if overall >= 4.2 and not has_critical_red_flags:
            recommendation = "STRONG_HIRE"
            reasoning = f"Candidate demonstrated outstanding technical depth (Score: {overall:.1f}/5.0) with verifiable production trade-offs and zero critical red flags."
        elif overall >= 3.5 and len(red_flags) <= 1:
            recommendation = "HIRE"
            reasoning = f"Solid technical performance (Score: {overall:.1f}/5.0) meeting role competencies across core domains with sound reasoning."
        elif overall >= 2.8:
            recommendation = "BORDERLINE"
            reasoning = f"Mixed signals (Score: {overall:.1f}/5.0). Candidate displayed theoretical understanding but struggled with edge-case failure mechanics."
        else:
            recommendation = "NO_HIRE"
            reasoning = f"Below technical bar (Score: {overall:.1f}/5.0). Multiple conceptual gaps or critical red flags identified during probing."

        report = EvidenceEvaluationReport(
            session_id=session.session_id,
            candidate_name=session.candidate_name,
            confidence_score=confidence,
            recommendation=recommendation,
            recommendation_reasoning=reasoning,
            key_strengths_with_evidence=unique_strengths,
            key_weaknesses_with_evidence=unique_weaknesses,
            red_flags=red_flags
        )

        logger.info("Generated Evidence Report", extra={
            "session_id": session.session_id,
            "recommendation": recommendation,
            "confidence": confidence,
            "red_flags_count": len(red_flags)
        })

        return report
