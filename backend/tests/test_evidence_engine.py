import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import (
    InterviewSession, InterviewConfig, InterviewStage, TranscriptEntry, TurnEvaluation
)
from app.interview.evidence_engine import EvidenceEvaluator

def test_evidence_quote_extraction_and_recommendation():
    eval_strong = TurnEvaluation(
        overall_score=4.6,
        correctness=4.8,
        depth_and_mechanics=4.7,
        communication_clarity=4.5,
        tradeoff_awareness=4.5,
        practical_vs_theory=4.5,
        strengths=["Deep understanding of optimistic lock versioning"],
        gaps=[],
        feedback="Strong"
    )

    t1 = TranscriptEntry(
        stage=InterviewStage.CORE_CONCEPTS,
        role="candidate",
        text="In our high-throughput cluster, we debugged a production deadlock caused by row locks, so we migrated to optimistic versioning with retry backoffs.",
        evaluation=eval_strong
    )

    session = InterviewSession(
        candidate_name="Alex Chen",
        config=InterviewConfig(),
        transcripts=[t1]
    )

    report = EvidenceEvaluator.extract_evidence_report(session)
    assert report.candidate_name == "Alex Chen"
    assert report.recommendation in ["STRONG_HIRE", "HIRE"]
    assert len(report.key_strengths_with_evidence) >= 1
    assert "optimistic versioning" in report.key_strengths_with_evidence[0].quote

def test_red_flag_detection_fatal_misconception():
    t_flag = TranscriptEntry(
        stage=InterviewStage.SYSTEM_DESIGN,
        role="candidate",
        text="We achieved zero latency and 100% ACID consistency across 5 microservices without distributed transactions.",
        evaluation=TurnEvaluation(overall_score=2.0, strengths=[], gaps=["Fatal misconception"])
    )

    session = InterviewSession(
        candidate_name="Bob",
        config=InterviewConfig(),
        transcripts=[t_flag]
    )

    report = EvidenceEvaluator.extract_evidence_report(session)
    assert len(report.red_flags) >= 1
    assert report.red_flags[0].category == "FATAL_MISCONCEPTION"
    assert report.red_flags[0].severity in ["HIGH", "CRITICAL"]
    assert report.recommendation in ["BORDERLINE", "NO_HIRE"]

def test_red_flag_detection_unsupported_claim():
    t_claim = TranscriptEntry(
        stage=InterviewStage.GREETING,
        role="candidate",
        text="I am an expert in distributed databases and lead the entire cluster architecture."
    )
    t_fail = TranscriptEntry(
        stage=InterviewStage.CORE_CONCEPTS,
        role="candidate",
        text="I don't know how MVCC or isolation levels work.",
        evaluation=TurnEvaluation(overall_score=1.5, strengths=[], gaps=["Did not understand basic isolation"])
    )

    session = InterviewSession(
        candidate_name="Charlie",
        config=InterviewConfig(),
        transcripts=[t_claim, t_fail]
    )

    report = EvidenceEvaluator.extract_evidence_report(session)
    assert any(rf.category == "UNSUPPORTED_CLAIM" for rf in report.red_flags)

@pytest.mark.asyncio
async def test_api_evidence_report_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_resp = await ac.post("/api/interview/session", json={
            "role": "Backend Engineer",
            "experience_level": "Senior / SDE-3 (5-8 years)"
        })
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # Run turn
        await ac.post("/api/voice/turn", json={
            "session_id": session_id,
            "text": "We solved deadlock contention by using CAS and atomic memory barriers in high-volume workloads."
        })

        # Fetch evidence report
        report_resp = await ac.get(f"/api/interview/session/{session_id}/evidence-report")
        assert report_resp.status_code == 200
        data = report_resp.json()
        assert data["session_id"] == session_id
        assert data["confidence_score"] > 0.0
        assert "recommendation" in data
