import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import InterviewConfig, InterviewStage, InterviewRole, ExperienceLevel
from app.interview.evaluation_engine import AnswerEvaluator, TurnEvaluation, SessionScorecard
from app.db.mongo import InterviewSessionRepository

def test_evaluate_turn_strong_production_answer():
    strong_reply = "In our high-throughput cluster, we debugged a production deadlock caused by row locks, so we migrated to optimistic versioning with retry backoffs. We accepted occasional rollback latency as a trade-off for eliminating lock contention."
    evaluation = AnswerEvaluator.evaluate_turn(
        candidate_reply=strong_reply,
        topic="Operating Systems & Concurrency",
        stage=InterviewStage.CORE_CONCEPTS
    )

    assert evaluation.overall_score >= 4.0
    assert evaluation.correctness >= 4.0
    assert evaluation.tradeoff_awareness >= 4.0
    assert evaluation.practical_vs_theory >= 4.0
    assert len(evaluation.strengths) >= 2

def test_evaluate_turn_shallow_answer():
    shallow_reply = "We just used Redis."
    evaluation = AnswerEvaluator.evaluate_turn(
        candidate_reply=shallow_reply,
        topic="Caching & Redis",
        stage=InterviewStage.CORE_CONCEPTS
    )

    assert evaluation.overall_score <= 3.0
    assert evaluation.depth_and_mechanics <= 2.5
    assert len(evaluation.gaps) >= 1

def test_evaluate_turn_confused_answer():
    confused_reply = "I don't know about that."
    evaluation = AnswerEvaluator.evaluate_turn(
        candidate_reply=confused_reply,
        topic="Distributed Systems",
        stage=InterviewStage.CORE_CONCEPTS
    )

    assert evaluation.overall_score <= 2.0
    assert evaluation.correctness <= 2.0
    assert "unable to answer" in evaluation.feedback.lower()

def test_session_scorecard_aggregation():
    eval1 = TurnEvaluation(
        overall_score=4.5,
        correctness=4.8,
        depth_and_mechanics=4.5,
        communication_clarity=4.5,
        tradeoff_awareness=4.5,
        practical_vs_theory=4.2,
        strengths=["Deep understanding of MVCC", "Great trade-off awareness"],
        gaps=[],
        feedback="Excellent"
    )
    eval2 = TurnEvaluation(
        overall_score=4.1,
        correctness=4.0,
        depth_and_mechanics=4.0,
        communication_clarity=4.0,
        tradeoff_awareness=4.2,
        practical_vs_theory=4.0,
        strengths=["Clear explanation of Kafka partitions"],
        gaps=["Could add more metrics"],
        feedback="Solid"
    )

    scorecard = AnswerEvaluator.aggregate_scorecard([eval1, eval2])
    assert scorecard.overall_score == 4.3
    assert scorecard.total_evaluated_turns == 2
    assert scorecard.passed_recommendation is True
    assert "Hire" in scorecard.summary_verdict
    assert len(scorecard.top_strengths) >= 2

@pytest.mark.asyncio
async def test_api_session_scorecard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session
        create_resp = await ac.post("/api/interview/session", json={
            "role": "Backend Engineer",
            "experience_level": "SDE-2 (2-5 years)",
            "topics": ["DBMS & SQL", "Caching & Redis"]
        })
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # Run a turn to generate evaluation
        turn_resp = await ac.post("/api/voice/turn", json={
            "session_id": session_id,
            "text": "We used PostgreSQL read replicas and covered indexes to optimize latency, accepting write overhead as a trade-off."
        })
        assert turn_resp.status_code == 200
        turn_data = turn_resp.json()
        assert turn_data["turn_evaluation"] is not None

        # Fetch scorecard
        score_resp = await ac.get(f"/api/interview/session/{session_id}/scorecard")
        assert score_resp.status_code == 200
        sc = score_resp.json()
        assert sc["total_evaluated_turns"] >= 1
