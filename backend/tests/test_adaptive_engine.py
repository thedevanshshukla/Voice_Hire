import pytest
from app.models.interview import InterviewConfig, InterviewStage, InterviewRole, ExperienceLevel
from app.interview.adaptive_engine import (
    AdaptiveQuestionEngine, AnswerDepth, AdaptiveStrategy, AdaptiveAction
)
from app.interview.prompt_builder import InterviewPromptBuilder

def test_evaluate_depth_classification():
    engine = AdaptiveQuestionEngine()

    # 1. Shallow keyword drop
    shallow_reply = "We just used Redis for caching."
    assert engine.evaluate_depth(shallow_reply) == AnswerDepth.SHALLOW_OR_VAGUE

    # 2. Confused answer
    confused_reply = "I'm not sure about that."
    assert engine.evaluate_depth(confused_reply) == AnswerDepth.INCORRECT_OR_CONFUSED

    # 3. Moderate answer
    moderate_reply = "We used composite B-Tree indexes on user_id and created_at to optimize query latency."
    assert engine.evaluate_depth(moderate_reply) == AnswerDepth.MODERATE

    # 4. Strong comprehensive answer with trade-offs & mechanics (>= 30 words)
    strong_reply = "We chose an optimistic locking pattern with version timestamps instead of pessimistic row locks to avoid deadlocks under high concurrency, accepting rollback retry latency as a trade-off for higher throughput."
    assert engine.evaluate_depth(strong_reply) == AnswerDepth.STRONG_OR_COMPREHENSIVE

def test_adaptive_probe_shallow_redis():
    engine = AdaptiveQuestionEngine(config=InterviewConfig(topics=["Caching & Redis", "DBMS & SQL"]))
    action = engine.analyze_turn_and_plan(
        last_candidate_reply="We simply added Redis to speed up queries.",
        current_stage=InterviewStage.CORE_CONCEPTS
    )

    assert action.evaluated_depth == AnswerDepth.SHALLOW_OR_VAGUE
    assert action.strategy == AdaptiveStrategy.PROBE_DEEPER
    assert "cache stampede" in action.guidance_directive.lower() or "invalidation" in action.guidance_directive.lower()

def test_adaptive_topic_rotation_on_mastery():
    config = InterviewConfig(topics=["DBMS & SQL", "Caching & Redis", "Distributed Systems"])
    engine = AdaptiveQuestionEngine(config=config)

    assert engine.get_active_topic() == "DBMS & SQL"

    # Turn 1: Strong comprehensive answer on DBMS (>= 30 words with trade-offs)
    action1 = engine.analyze_turn_and_plan(
        last_candidate_reply="We configured PostgreSQL read replicas with covered B-Tree indexing to lower query latency, evaluating index selectivity with EXPLAIN ANALYZE while balancing write-amplification trade-offs on high-volume update workloads.",
        current_stage=InterviewStage.CORE_CONCEPTS
    )
    assert action1.strategy == AdaptiveStrategy.INCREASE_DIFFICULTY
    assert engine.get_active_topic() == "DBMS & SQL"

    # Turn 2: Another strong comprehensive answer on DBMS -> triggers topic rotation to Caching & Redis!
    action2 = engine.analyze_turn_and_plan(
        last_candidate_reply="To prevent serialization isolation anomalies and deadlocks, we used explicit transaction rollbacks with retries and carefully tuned table vacuuming to eliminate MVCC bloat and maintain high consistency.",
        current_stage=InterviewStage.CORE_CONCEPTS
    )
    assert action2.strategy == AdaptiveStrategy.PIVOT_NEXT_TOPIC
    assert action2.target_topic == "Caching & Redis"
    assert engine.get_active_topic() == "Caching & Redis"

def test_prompt_builder_with_adaptive_action():
    config = InterviewConfig(role=InterviewRole.BACKEND, experience_level=ExperienceLevel.MID)
    action = AdaptiveAction(
        evaluated_depth=AnswerDepth.SHALLOW_OR_VAGUE,
        strategy=AdaptiveStrategy.PROBE_DEEPER,
        target_topic="Caching & Redis",
        strategy_display="🔍 Probing Depth",
        guidance_directive="[ADAPTIVE DIRECTIVE: PROBE DEEPER] Challenge candidate on cache stampede and TTL expiry spikes."
    )
    
    prompt = InterviewPromptBuilder.build_system_prompt(
        config=config,
        candidate_name="Alex",
        stage=InterviewStage.CORE_CONCEPTS,
        adaptive_action=action
    )
    assert "[ADAPTIVE DIRECTIVE: PROBE DEEPER]" in prompt
    assert "cache stampede" in prompt
