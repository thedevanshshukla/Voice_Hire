import asyncio
from typing import AsyncIterator, List, Optional
from pydantic import BaseModel

from app.voice.stt.base import BaseSTTProvider, STTTranscriptionResult
from app.voice.llm.base import BaseLLMProvider, LLMMessage
from app.voice.tts.base import BaseTTSProvider
from app.voice.vad.turn_detector import TurnDetector, TurnDetectionResult, TurnStatus
from app.voice.interruption.cancellation import CancellationToken, InterruptedException
from app.voice.interruption.barge_in import BargeInDetector, BargeInResult
from app.voice.factory import VoiceProviderFactory
from app.voice.chunker import SentenceBoundaryChunker
from app.core.telemetry import StreamingMetricsTracker, TurnLatencyMetrics
from app.core.logger import get_logger

logger = get_logger("voice.streaming_pipeline")

class StreamAudioEvent(BaseModel):
    event_type: str # "vad_event", "transcript", "token", "audio_chunk", "interrupted", "metrics", "done"
    vad_status: Optional[str] = None
    text: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    audio_format: str = "wav"
    metrics: Optional[TurnLatencyMetrics] = None

class StreamingVoicePipeline:
    """
    Streaming Voice AI Pipeline coordinating:
    VAD / Turn Detection -> Audio In -> STT -> Streaming LLM -> Sentence Chunker -> Streaming TTS -> Barge-In Monitoring -> Audio Out.
    """
    def __init__(
        self,
        stt: Optional[BaseSTTProvider] = None,
        llm: Optional[BaseLLMProvider] = None,
        tts: Optional[BaseTTSProvider] = None,
        turn_detector: Optional[TurnDetector] = None,
        barge_in_detector: Optional[BargeInDetector] = None
    ):
        self.stt = stt or VoiceProviderFactory.get_stt_provider()
        self.llm = llm or VoiceProviderFactory.get_llm_provider()
        self.tts = tts or VoiceProviderFactory.get_tts_provider()
        self.turn_detector = turn_detector or TurnDetector()
        self.barge_in_detector = barge_in_detector or BargeInDetector()

    async def stream_turn(
        self,
        audio_stream: Optional[AsyncIterator[bytes]] = None,
        raw_audio: Optional[bytes] = None,
        input_text: Optional[str] = None,
        history: Optional[List[LLMMessage]] = None,
        system_prompt: Optional[str] = None,
        language: str = "en",
        cancellation_token: Optional[CancellationToken] = None
    ) -> AsyncIterator[StreamAudioEvent]:
        tracker = StreamingMetricsTracker()
        token = cancellation_token or CancellationToken()
        
        # 1. VAD & STT Phase
        tracker.mark_stt_start()
        
        if raw_audio and len(raw_audio) > 100:
            frame_size = 640
            for i in range(0, len(raw_audio), frame_size):
                if token.is_cancelled:
                    break
                frame = raw_audio[i:i + frame_size]
                det_res = self.turn_detector.process_frame(frame)
                yield StreamAudioEvent(event_type="vad_event", vad_status=det_res.status.value)
            
            tracker.set_turn_vad_metrics(
                speech_ms=self.turn_detector.total_speech_ms,
                pause_count=self.turn_detector.pause_count,
                endpointing_ms=self.turn_detector.current_silence_ms
            )

        if token.is_cancelled:
            yield StreamAudioEvent(event_type="interrupted")
            return

        if input_text:
            transcript = input_text
            tracker.mark_stt_end()
            yield StreamAudioEvent(event_type="transcript", text=transcript)
        elif raw_audio:
            stt_res = await self.stt.transcribe(raw_audio, language=language)
            transcript = stt_res.text
            tracker.mark_stt_end()
            yield StreamAudioEvent(event_type="transcript", text=transcript)
        elif audio_stream:
            async for partial in self.stt.stream_transcribe(audio_stream, language=language):
                if token.is_cancelled:
                    yield StreamAudioEvent(event_type="interrupted")
                    return
                if partial.is_final:
                    transcript = partial.text
                    tracker.mark_stt_end()
                    yield StreamAudioEvent(event_type="transcript", text=transcript)
                else:
                    yield StreamAudioEvent(event_type="partial_transcript", text=partial.text)
        else:
            transcript = "Hello."
            tracker.mark_stt_end()
            yield StreamAudioEvent(event_type="transcript", text=transcript)

        # 2. LLM Streaming & Barge-in Phase
        messages = list(history or [])
        messages.append(LLMMessage(role="user", content=transcript))
        
        tracker.mark_llm_start()
        self.barge_in_detector.set_agent_state(is_active=True)

        # 3. Sentence Boundary Chunker -> Streaming TTS
        chunker = SentenceBoundaryChunker()
        full_text = []
        tracker.mark_tts_start()

        try:
            async for chunk in chunker.process_stream(self.llm.stream_response(messages, system_prompt=system_prompt)):
                if token.is_cancelled:
                    tracker.record_interruption(
                        detection_ms=120.0,
                        cancellation_ms=token.cancellation_latency_ms,
                        word=chunk[:20]
                    )
                    yield StreamAudioEvent(event_type="interrupted", text=chunk)
                    break

                tracker.mark_llm_first_token()
                full_text.append(chunk)
                yield StreamAudioEvent(event_type="token", text=chunk + " ")
                
                # Stream TTS audio for this sentence chunk
                async for audio_chunk in self.tts.stream_synthesize(chunk):
                    if token.is_cancelled:
                        tracker.record_interruption(
                            detection_ms=120.0,
                            cancellation_ms=token.cancellation_latency_ms,
                            word=chunk[:20]
                        )
                        yield StreamAudioEvent(event_type="interrupted")
                        break

                    tracker.mark_tts_first_audio()
                    yield StreamAudioEvent(
                        event_type="audio_chunk",
                        audio_bytes=audio_chunk,
                        audio_format="wav" if getattr(self.tts, "format", "wav") == "wav" else "mp3"
                    )

                if token.is_cancelled:
                    break

        except InterruptedException:
            yield StreamAudioEvent(event_type="interrupted")
        finally:
            self.barge_in_detector.set_agent_state(is_active=False)

        tracker.mark_tts_end()
        metrics = tracker.compute_metrics()

        yield StreamAudioEvent(
            event_type="metrics",
            metrics=metrics,
            text=" ".join(full_text)
        )
        yield StreamAudioEvent(event_type="done")
