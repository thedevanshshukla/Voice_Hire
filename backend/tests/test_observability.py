import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.observability.telemetry import TurnSpan, MetricsExporter

def test_turn_span_recording_and_metrics():
    span = TurnSpan(
        session_id="sess-test-obs",
        turn_index=1,
        stt_latency_ms=120.0,
        llm_ttft_ms=180.0,
        llm_total_ms=450.0,
        tts_ttfa_ms=220.0,
        tts_total_ms=600.0,
        was_interrupted=False
    )
    time.sleep(0.01)
    MetricsExporter.record_span(span)

    stats = MetricsExporter.get_summary_stats()
    assert stats["total_turns"] >= 1
    assert stats["avg_llm_ttft_ms"] > 0
    assert stats["avg_tts_ttfa_ms"] > 0

    prom_text = MetricsExporter.generate_prometheus_metrics()
    assert "voicehire_turns_total" in prom_text
    assert "voicehire_llm_ttft_ms_avg" in prom_text

@pytest.mark.asyncio
async def test_api_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/metrics")
        assert resp.status_code == 200
        assert "voicehire_turns_total" in resp.text
