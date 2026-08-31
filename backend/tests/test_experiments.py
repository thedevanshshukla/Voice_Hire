import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.experiments.ab_engine import ABExperimentManager

def test_ab_experiment_assignment():
    ABExperimentManager.initialize_defaults()
    exps = ABExperimentManager.get_active_experiments()
    assert len(exps) >= 2

    # Deterministic assignment test
    sess_id = "sess-ab-test-42"
    assign1 = ABExperimentManager.assign_variants(sess_id)
    assign2 = ABExperimentManager.assign_variants(sess_id)
    assert assign1 == assign2
    assert "exp_llm_model" in assign1

def test_ab_experiment_metrics_recording():
    ABExperimentManager.record_metric(
        experiment_id="exp_llm_model",
        variant_id="control_gemini",
        turn_latency_ms=320.0,
        ttft_ms=160.0,
        scorecard_score=4.2
    )

    res = ABExperimentManager.get_experiment_results("exp_llm_model")
    assert res is not None
    assert res.total_sessions_allocated >= 1
    control_perf = next((v for v in res.variant_performances if v.variant_id == "control_gemini"), None)
    assert control_perf is not None
    assert control_perf.sample_count >= 1
    assert control_perf.avg_ttft_ms > 0

@pytest.mark.asyncio
async def test_api_experiments_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_resp = await ac.get("/api/experiments/active")
        assert list_resp.status_code == 200
        exps = list_resp.json()
        assert len(exps) >= 2

        results_resp = await ac.get("/api/experiments/exp_llm_model/results")
        assert results_resp.status_code == 200
        res_data = results_resp.json()
        assert res_data["experiment_id"] == "exp_llm_model"
