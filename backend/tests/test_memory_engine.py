import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import InterviewSession, InterviewConfig, InterviewStage, SessionScorecard
from app.interview.memory_engine import InterviewMemoryEngine, CandidateProfileRepository

def test_memory_claim_extraction():
    engine = InterviewMemoryEngine()
    
    contras = engine.process_candidate_turn(
        candidate_text="In our past project we used PostgreSQL with optimistic locking and Redis for caching.",
        turn_index=1,
        stage=InterviewStage.RESUME_DEEP_DIVE
    )

    assert len(contras) == 0
    assert len(engine.memory.claims) >= 2
    assert "PostgreSQL" in engine.memory.mentioned_technologies
    assert "Redis" in engine.memory.mentioned_technologies

def test_memory_contradiction_detection():
    engine = InterviewMemoryEngine()

    # Turn 1: Claims Kafka
    engine.process_candidate_turn(
        candidate_text="We used Kafka for asynchronous event ordering across our microservices.",
        turn_index=1,
        stage=InterviewStage.RESUME_DEEP_DIVE
    )

    # Turn 2: Direct contradiction
    contras = engine.process_candidate_turn(
        candidate_text="We never used Kafka or any message queue in our backend architecture.",
        turn_index=2,
        stage=InterviewStage.CORE_CONCEPTS
    )

    assert len(contras) >= 1
    assert "Kafka" in contras[0].earlier_claim
    assert "Contradicted earlier claim" in contras[0].explanation

def test_memory_cross_turn_reference():
    engine = InterviewMemoryEngine()
    engine.process_candidate_turn(
        candidate_text="We configured Redis caching with TTL jitter to eliminate stampedes.",
        turn_index=1,
        stage=InterviewStage.RESUME_DEEP_DIVE
    )

    callback = engine.generate_cross_turn_reference(current_topic="Caching & Redis")
    assert callback is not None
    assert "Redis" in callback
    assert "CROSS-TURN MEMORY CALLBACK DIRECTIVE" in callback

def test_long_term_candidate_profile_repository():
    session1 = InterviewSession(
        session_id="sess-round-1",
        candidate_id="cand-alex-99",
        candidate_name="Alex Chen",
        config=InterviewConfig(),
        scorecard=SessionScorecard(overall_score=4.1, summary_verdict="Hire", top_strengths=["Optimistic Locks"])
    )

    profile1 = CandidateProfileRepository.record_session_completion(session1)
    assert profile1.candidate_id == "cand-alex-99"
    assert len(profile1.round_progression) == 1
    assert profile1.round_progression[0]["round"] == 1
    assert "Optimistic Locks" in profile1.cumulative_strengths

    # Round 2 completion
    session2 = InterviewSession(
        session_id="sess-round-2",
        candidate_id="cand-alex-99",
        candidate_name="Alex Chen",
        config=InterviewConfig(),
        scorecard=SessionScorecard(overall_score=4.5, summary_verdict="Strong Hire", top_strengths=["Distributed Sharding"])
    )
    profile2 = CandidateProfileRepository.record_session_completion(session2)
    assert len(profile2.round_progression) == 2
    assert "Distributed Sharding" in profile2.cumulative_strengths

@pytest.mark.asyncio
async def test_api_memory_and_profile_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create session
        create_resp = await ac.post("/api/interview/session", json={
            "role": "Backend Engineer",
            "experience_level": "SDE-2 (2-5 years)"
        })
        assert create_resp.status_code == 200
        session_data = create_resp.json()
        session_id = session_data["session_id"]
        candidate_id = session_data["candidate_id"]

        # Run turn with claim
        turn_resp = await ac.post("/api/voice/turn", json={
            "session_id": session_id,
            "text": "We used PostgreSQL and Redis clusters for our primary storage layer."
        })
        assert turn_resp.status_code == 200
        assert turn_resp.json()["memory_claims_count"] >= 1

        # Query memory endpoint
        mem_resp = await ac.get(f"/api/interview/session/{session_id}/memory")
        assert mem_resp.status_code == 200
        mem = mem_resp.json()
        assert len(mem["claims"]) >= 1

        # Query candidate profile endpoint
        prof_resp = await ac.get(f"/api/interview/candidate/{candidate_id}/profile")
        assert prof_resp.status_code == 200
        prof = prof_resp.json()
        assert prof["candidate_id"] == candidate_id
