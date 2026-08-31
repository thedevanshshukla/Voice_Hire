import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.interview import InterviewConfig, InterviewStage, InterviewRole, ExperienceLevel
from app.interview.state_machine import (
    InterviewStateMachine, STAGE_SEQUENCE, STAGE_DISPLAY_NAMES, StageBudget
)
from app.interview.prompt_builder import InterviewPromptBuilder

def test_state_machine_stage_budgets_30_min():
    config = InterviewConfig(duration_minutes=30)
    sm = InterviewStateMachine(config=config)
    budgets = sm.get_budgets()

    assert len(budgets) == 6
    greeting_budget = next(b for b in budgets if b.stage == InterviewStage.GREETING)
    assert greeting_budget.target_duration_minutes == 3.0
    
    core_budget = next(b for b in budgets if b.stage == InterviewStage.CORE_CONCEPTS)
    assert core_budget.target_duration_minutes == 10.5

    sd_budget = next(b for b in budgets if b.stage == InterviewStage.SYSTEM_DESIGN)
    assert sd_budget.target_duration_minutes == 7.5

def test_state_machine_stage_progression():
    config = InterviewConfig(duration_minutes=30)
    sm = InterviewStateMachine(config=config, initial_stage=InterviewStage.GREETING)

    assert sm.current_stage == InterviewStage.GREETING
    assert sm.total_turns == 0

    # Turn 1: Greeting turn with substantial background -> Advances to RESUME_DEEP_DIVE
    res1 = sm.step_turn(last_candidate_reply="Hi, I am Alex. I have 4 years of experience as a Backend engineer working with distributed microservices, Go, and PostgreSQL.")
    assert res1.previous_stage == InterviewStage.GREETING
    assert res1.current_stage == InterviewStage.RESUME_DEEP_DIVE
    assert res1.transitioned is True
    assert res1.progress_pct > 16.0

    # Resume Deep Dive: Max 3 turns
    sm.step_turn(last_candidate_reply="I led the migration from a monolith to event-driven microservices.")
    sm.step_turn(last_candidate_reply="We used Kafka for ordering guarantees.")
    res_resume_end = sm.step_turn(last_candidate_reply="We used Redis for caching.")
    assert res_resume_end.current_stage == InterviewStage.CORE_CONCEPTS

    # Step through Core Concepts (Max 5 turns)
    for _ in range(5):
        sm.step_turn(last_candidate_reply="We use optimistic locking with version timestamps.")
    assert sm.current_stage == InterviewStage.SYSTEM_DESIGN

    # Step through System Design (Max 4 turns)
    for _ in range(4):
        sm.step_turn(last_candidate_reply="We shard by user_id with consistent hashing.")
    assert sm.current_stage == InterviewStage.CANDIDATE_QUESTIONS

    # Candidate Q&A concluding on "no further questions"
    res_qa = sm.step_turn(last_candidate_reply="No further questions from my side, thank you!")
    assert res_qa.current_stage == InterviewStage.WRAP_UP
    assert res_qa.progress_pct == 100.0

def test_prompt_builder_injects_stage_directive():
    config = InterviewConfig(role=InterviewRole.BACKEND, experience_level=ExperienceLevel.MID)
    
    # 1. System Design stage prompt
    sd_prompt = InterviewPromptBuilder.build_system_prompt(config, candidate_name="Alex", stage=InterviewStage.SYSTEM_DESIGN)
    assert "SYSTEM ARCHITECTURE & DESIGN" in sd_prompt
    assert "single points of failure" in sd_prompt

    # 2. Greeting stage prompt
    greet_prompt = InterviewPromptBuilder.build_system_prompt(config, candidate_name="Alex", stage=InterviewStage.GREETING)
    assert "INTRODUCTION & GREETING" in greet_prompt

@pytest.mark.asyncio
async def test_api_interview_stages_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/interview/stages?duration_minutes=45")
        assert resp.status_code == 200
        stages = resp.json()
        assert len(stages) == 6
        core = next(s for s in stages if s["stage"] == "core_concepts")
        assert core["target_duration_minutes"] == round(45 * 0.35, 1) # 15.8 min
