import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import (
    InterviewRole, ExperienceLevel, InterviewLanguage, 
    InterviewConfig, InterviewSession, SessionStatus
)
from app.interview.prompt_builder import InterviewPromptBuilder
from app.db.mongo import InterviewSessionRepository

def test_interview_config_and_session_models():
    config = InterviewConfig(
        role=InterviewRole.BACKEND,
        experience_level=ExperienceLevel.MID,
        topics=["DBMS & SQL", "Caching & Redis"],
        duration_minutes=45,
        job_description="Seeking a Senior Go/Python backend engineer with distributed systems experience."
    )
    session = InterviewSession(
        candidate_name="Alex Chen",
        config=config
    )
    assert session.session_id.startswith("session-")
    assert session.candidate_name == "Alex Chen"
    assert session.config.role == InterviewRole.BACKEND
    assert session.status == SessionStatus.CONFIGURED
    assert len(session.config.topics) == 2

def test_interview_prompt_builder():
    config = InterviewConfig(
        role=InterviewRole.SYSTEM_DESIGN,
        experience_level=ExperienceLevel.STAFF,
        topics=["Distributed Systems", "Message Queues & Event Streaming"],
        job_description="Architect multi-region active-active clusters."
    )
    prompt = InterviewPromptBuilder.build_system_prompt(config, candidate_name="Sarah")
    
    assert "VoiceHire" in prompt
    assert "Distributed Systems Architect" in prompt
    assert "Staff / Principal" in prompt
    assert "Distributed Systems, Message Queues & Event Streaming" in prompt
    assert "Architect multi-region active-active clusters." in prompt
    assert "Sarah" in prompt

def test_interview_prompt_builder_hindi():
    config = InterviewConfig(
        role=InterviewRole.FRONTEND,
        experience_level=ExperienceLevel.JUNIOR,
        topics=["REST & GraphQL API Design"],
        language=InterviewLanguage.HINDI
    )
    prompt = InterviewPromptBuilder.build_system_prompt(config, candidate_name="Rahul")
    assert "Hindi" in prompt
    assert "Devanagari" in prompt

@pytest.mark.asyncio
async def test_interview_session_repository_crud():
    config = InterviewConfig(role=InterviewRole.DEVOPS, experience_level=ExperienceLevel.SENIOR)
    session = InterviewSession(candidate_name="DevOps Candidate", config=config)
    
    # 1. Create
    created = await InterviewSessionRepository.create_session(session)
    assert created.session_id == session.session_id

    # 2. Read
    fetched = await InterviewSessionRepository.get_session(session.session_id)
    assert fetched is not None
    assert fetched.candidate_name == "DevOps Candidate"
    assert fetched.config.role == InterviewRole.DEVOPS

    # 3. Update
    updated = await InterviewSessionRepository.update_session(session.session_id, {"status": SessionStatus.ACTIVE.value, "turn_count": 3})
    assert updated is not None
    assert updated.status == SessionStatus.ACTIVE
    assert updated.turn_count == 3

    # 4. List
    sessions = await InterviewSessionRepository.list_sessions(limit=10)
    assert any(s.session_id == session.session_id for s in sessions)

@pytest.mark.asyncio
async def test_interview_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Templates
        resp = await ac.get("/api/interview/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "roles" in data
        assert "experience_levels" in data
        assert "Backend Engineer" in data["roles"]

        # 2. Create Session
        create_resp = await ac.post("/api/interview/session", json={
            "role": "Backend Engineer",
            "experience_level": "SDE-2 (2-5 years)",
            "topics": ["DBMS & SQL", "Caching & Redis"],
            "duration_minutes": 30
        })
        assert create_resp.status_code == 200
        session_data = create_resp.json()
        assert "session_id" in session_data
        session_id = session_data["session_id"]

        # 3. Get Session
        get_resp = await ac.get(f"/api/interview/session/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["session_id"] == session_id

        # 4. List Sessions
        list_resp = await ac.get("/api/interview/sessions")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1
