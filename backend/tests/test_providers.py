import pytest
from app.voice.stt.providers.mock import MockSTTProvider
from app.voice.llm.providers.mock import MockLLMProvider
from app.voice.llm.base import LLMMessage
from app.voice.tts.providers.mock import MockTTSProvider
from app.voice.factory import VoiceProviderFactory
from app.voice.pipeline import BasicVoicePipeline

@pytest.mark.asyncio
async def test_mock_stt_transcription():
    stt = MockSTTProvider(default_response="Explain CAP theorem.")
    result = await stt.transcribe(b"\x00" * 100, language="en")
    assert result.text == "Explain CAP theorem."
    assert result.is_final is True
    assert result.confidence > 0.9

@pytest.mark.asyncio
async def test_mock_llm_response():
    llm = MockLLMProvider()
    messages = [LLMMessage(role="user", content="What is CAP theorem?")]
    response = await llm.generate_response(messages)
    assert "CAP theorem" in response.content or "Thank you" in response.content
    assert response.tokens_used > 0

@pytest.mark.asyncio
async def test_mock_tts_synthesis():
    tts = MockTTSProvider()
    result = await tts.synthesize("CAP theorem states consistency, availability, partition tolerance.")
    assert len(result.audio_bytes) > 44  # Valid WAV header + data
    assert result.format == "wav"
    assert result.sample_rate == 24000

@pytest.mark.asyncio
async def test_voice_pipeline_turn():
    pipeline = BasicVoicePipeline(
        stt=MockSTTProvider(default_response="PostgreSQL indexing"),
        llm=MockLLMProvider(),
        tts=MockTTSProvider()
    )
    result = await pipeline.process_turn(audio_in=b"\x00" * 200, language="en")
    assert result.transcript == "PostgreSQL indexing"
    assert len(result.response_text) > 0
    assert len(result.audio_bytes) > 44
    assert result.metrics.total_latency_ms > 0
    assert result.metrics.stt_latency_ms >= 0
    assert result.metrics.llm_latency_ms >= 0
    assert result.metrics.tts_latency_ms >= 0

def test_provider_factory():
    stt = VoiceProviderFactory.get_stt_provider("mock")
    llm = VoiceProviderFactory.get_llm_provider("mock")
    tts = VoiceProviderFactory.get_tts_provider("mock")
    
    assert isinstance(stt, MockSTTProvider)
    assert isinstance(llm, MockLLMProvider)
    assert isinstance(tts, MockTTSProvider)
