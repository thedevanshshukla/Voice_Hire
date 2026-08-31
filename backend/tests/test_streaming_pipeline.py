import pytest
import asyncio
from app.voice.chunker import SentenceBoundaryChunker
from app.core.telemetry import StreamingMetricsTracker
from app.voice.streaming_pipeline import StreamingVoicePipeline
from app.voice.stt.providers.mock import MockSTTProvider
from app.voice.llm.providers.mock import MockLLMProvider
from app.voice.tts.providers.mock import MockTTSProvider

@pytest.mark.asyncio
async def test_sentence_boundary_chunker():
    chunker = SentenceBoundaryChunker()
    
    async def sample_token_stream():
        tokens = ["Hello", " ", "there!", " ", "This", " ", "is", " ", "sentence", " ", "two.", " ", "Done."]
        for t in tokens:
            await asyncio.sleep(0.01)
            yield t

    chunks = []
    async for chunk in chunker.process_stream(sample_token_stream()):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert chunks[0] == "Hello there!"
    assert chunks[1] == "This is sentence two."
    assert chunks[2] == "Done."

def test_streaming_metrics_tracker():
    tracker = StreamingMetricsTracker()
    tracker.mark_stt_start()
    tracker.mark_stt_end()
    
    tracker.mark_llm_start()
    tracker.mark_llm_first_token()
    tracker.mark_llm_end()
    
    tracker.mark_tts_start()
    tracker.mark_tts_first_audio()
    tracker.mark_tts_end()
    
    metrics = tracker.compute_metrics()
    assert metrics.stt_latency_ms >= 0.0
    assert metrics.llm_ttft_ms >= 0.0
    assert metrics.tts_ttfa_ms >= 0.0
    assert metrics.total_turn_ms >= 0.0

@pytest.mark.asyncio
async def test_streaming_voice_pipeline():
    pipeline = StreamingVoicePipeline(
        stt=MockSTTProvider(default_response="Explain ACID properties."),
        llm=MockLLMProvider(default_reply="ACID stands for Atomicity, Consistency, Isolation, Durability."),
        tts=MockTTSProvider()
    )
    
    events = []
    async for event in pipeline.stream_turn(input_text="Explain ACID properties."):
        events.append(event)
        
    event_types = [e.event_type for e in events]
    assert "transcript" in event_types
    assert "token" in event_types
    assert "audio_chunk" in event_types
    assert "metrics" in event_types
    assert "done" in event_types
    
    metrics_event = next(e for e in events if e.event_type == "metrics")
    assert metrics_event.metrics is not None
    assert metrics_event.metrics.total_turn_ms > 0
