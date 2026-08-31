import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.2.0"
        assert "providers" in data

@pytest.mark.asyncio
async def test_voice_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/voice/status")
        assert response.status_code == 200
        data = response.json()
        assert "livekit_url" in data
        assert "providers" in data

@pytest.mark.asyncio
async def test_livekit_token_generation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "room_name": "interview-sde1-001",
            "identity": "candidate-alice",
            "name": "Alice Developer"
        }
        response = await client.post("/api/voice/token", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 20
        assert data["room_name"] == "interview-sde1-001"
        assert data["identity"] == "candidate-alice"

@pytest.mark.asyncio
async def test_voice_turn_processing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "What is the difference between TCP and UDP?",
            "language": "en"
        }
        response = await client.post("/api/voice/turn", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "transcript" in data
        assert "response_text" in data
        assert "audio_base64" in data
        assert "metrics" in data
        assert data["metrics"]["total_latency_ms"] > 0
