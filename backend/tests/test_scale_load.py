import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.scale import LoadTestConfig
from app.scale.load_runner import ConcurrentLoadSimulator

@pytest.mark.asyncio
async def test_concurrent_load_simulation():
    config = LoadTestConfig(concurrent_sessions=5, turns_per_session=2)
    res = await ConcurrentLoadSimulator.run_load_test(config)

    assert res.total_turns_simulated == 10
    assert res.successful_turns == 10
    assert res.failed_turns == 0
    assert res.throughput_tps > 0
    assert res.p50_latency_ms > 0
    assert res.p95_latency_ms >= res.p50_latency_ms

@pytest.mark.asyncio
async def test_api_scale_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Run load test endpoint
        run_resp = await ac.post("/api/scale/run-load-test", json={
            "concurrent_sessions": 4,
            "turns_per_session": 2
        })
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["total_turns_simulated"] == 8
        assert run_data["successful_turns"] == 8

        # Get results endpoint
        res_resp = await ac.get("/api/scale/load-test-results")
        assert res_resp.status_code == 200
        res_data = res_resp.json()
        assert res_data["total_turns_simulated"] >= 8
