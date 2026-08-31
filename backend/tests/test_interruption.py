import pytest
import asyncio
import struct
from app.voice.interruption.cancellation import CancellationToken, InterruptedException
from app.voice.interruption.barge_in import BargeInDetector, BargeInResult
from app.voice.vad.providers.energy import EnergyVADProvider
from app.voice.streaming_pipeline import StreamingVoicePipeline
from app.voice.stt.providers.mock import MockSTTProvider
from app.voice.llm.providers.mock import MockLLMProvider
from app.voice.tts.providers.mock import MockTTSProvider

def generate_pcm_frame(amplitude: int = 0, num_samples: int = 320) -> bytes:
    """Generate 20ms of 16-bit PCM samples at 16kHz."""
    return struct.pack(f"<{num_samples}h", *([amplitude] * num_samples))

def test_cancellation_token_lifecycle():
    token = CancellationToken()
    assert token.is_cancelled is False

    callback_called = False
    def on_cancel():
        nonlocal callback_called
        callback_called = True

    token.on_cancel(on_cancel)
    token.cancel(reason="test_barge_in")

    assert token.is_cancelled is True
    assert callback_called is True
    assert token.cancellation_latency_ms >= 0.0

    with pytest.raises(InterruptedException):
        token.raise_if_cancelled()

def test_barge_in_detector_active_speech_cancellation():
    detector = BargeInDetector(
        vad_provider=EnergyVADProvider(energy_threshold=0.01),
        min_speech_duration_ms=100
    )
    token = CancellationToken()

    # 1. Agent is NOT active -> Candidate speech does not trigger barge-in
    detector.set_agent_state(is_active=False)
    speech_frame = generate_pcm_frame(amplitude=8000)
    for _ in range(10):
        res = detector.process_frame(speech_frame, cancellation_token=token)
    assert res.is_interrupted is False
    assert token.is_cancelled is False

    # 2. Agent becomes active (speaking) -> Silence from candidate does not interrupt
    detector.set_agent_state(is_active=True)
    silence_frame = generate_pcm_frame(amplitude=0)
    for _ in range(10):
        res = detector.process_frame(silence_frame, cancellation_token=token)
    assert res.is_interrupted is False
    assert token.is_cancelled is False

    # 3. Candidate speaks while agent is active (> 100ms) -> Triggers barge-in
    final_res = None
    for _ in range(6): # 6 frames x 20ms = 120ms
        final_res = detector.process_frame(speech_frame, cancellation_token=token)
        if final_res.is_interrupted:
            break

    assert final_res is not None
    assert final_res.is_interrupted is True
    assert token.is_cancelled is True
    assert detector.interruption_count == 1

@pytest.mark.asyncio
async def test_streaming_pipeline_mid_stream_interruption():
    pipeline = StreamingVoicePipeline(
        stt=MockSTTProvider(default_response="Explain CAP theorem."),
        llm=MockLLMProvider(default_reply="Consistency, Availability, Partition tolerance are the three main pillars."),
        tts=MockTTSProvider()
    )

    token = CancellationToken()
    
    # Trigger cancellation after brief delay
    async def trigger_cancel():
        await asyncio.sleep(0.04)
        token.cancel(reason="test_interrupt")

    asyncio.create_task(trigger_cancel())

    events = []
    async for event in pipeline.stream_turn(input_text="Explain CAP theorem.", cancellation_token=token):
        events.append(event)

    event_types = [e.event_type for e in events]
    assert "interrupted" in event_types
