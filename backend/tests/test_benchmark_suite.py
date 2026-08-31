import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.evaluation.benchmark_runner import BenchmarkRunner

def test_benchmark_runner_execution():
    summary = BenchmarkRunner.run_evaluation_suite()
    assert summary.total_samples == 4
    assert summary.mean_absolute_error <= 1.5
    assert summary.accuracy_within_half_point_pct >= 50.0
    assert summary.red_flag_precision >= 0.80
    assert len(summary.sample_results) == 4

@pytest.mark.asyncio
async def test_api_benchmark_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Run benchmark
        run_resp = await ac.post("/api/evaluation/run-benchmark")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["total_samples"] >= 4
        assert run_data["mean_absolute_error"] <= 1.5

        # Get results
        res_resp = await ac.get("/api/evaluation/benchmark-results")
        assert res_resp.status_code == 200
        res_data = res_resp.json()
        assert res_data["total_samples"] >= 4
