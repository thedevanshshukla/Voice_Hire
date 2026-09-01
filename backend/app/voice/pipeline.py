import time
from typing import List, Optional
from pydantic import BaseModel

from app.voice.stt.base import BaseSTTProvider
from app.voice.llm.base import BaseLLMProvider, LLMMessage
from app.voice.tts.base import BaseTTSProvider
from app.voice.factory import VoiceProviderFactory
from app.core.logger import get_logger

logger = get_logger("voice.pipeline")

class PipelineTurnMetrics(BaseModel):
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

class PipelineTurnResult(BaseModel):
    transcript: str
    response_text: str
    audio_bytes: bytes
    audio_format: str
    metrics: PipelineTurnMetrics

class BasicVoicePipeline:
    """
    Core Voice Pipeline coordinating STT -> LLM -> TTS execution with latency tracking.
    """
    def __init__(
        self,
        stt: Optional[BaseSTTProvider] = None,
        llm: Optional[BaseLLMProvider] = None,
        tts: Optional[BaseTTSProvider] = None
    ):
        self.stt = stt or VoiceProviderFactory.get_stt_provider()
        self.llm = llm or VoiceProviderFactory.get_llm_provider()
        self.tts = tts or VoiceProviderFactory.get_tts_provider()

    async def process_turn(
        self,
        audio_in: Optional[bytes] = None,
        input_text: Optional[str] = None,
        history: Optional[List[LLMMessage]] = None,
        system_prompt: Optional[str] = None,
        language: str = "en"
    ) -> PipelineTurnResult:
        total_start = time.perf_counter()
        
        # 1. STT Phase
        stt_start = time.perf_counter()
        if input_text is not None:
            transcript = input_text
            stt_latency = 0.0
        elif audio_in:
            stt_result = await self.stt.transcribe(audio_in, language=language)
            transcript = stt_result.text
            stt_latency = (time.perf_counter() - stt_start) * 1000.0
        else:
            transcript = ""
            stt_latency = 0.0
        
        logger.info("STT Transcription completed", extra={
            "transcript": transcript,
            "stt_latency_ms": round(stt_latency, 2)
        })

        # 2. LLM Phase
        llm_messages = list(history or [])
        if transcript:
            llm_messages.append(LLMMessage(role="user", content=transcript))
        
        llm_start = time.perf_counter()
        llm_result = await self.llm.generate_response(
            messages=llm_messages,
            system_prompt=system_prompt
        )
        llm_latency = (time.perf_counter() - llm_start) * 1000.0
        
        logger.info("LLM Generation completed", extra={
            "response": llm_result.content,
            "llm_latency_ms": round(llm_latency, 2),
            "tokens": llm_result.tokens_used
        })

        # 3. TTS Phase
        tts_start = time.perf_counter()
        tts_result = await self.tts.synthesize(llm_result.content)
        tts_latency = (time.perf_counter() - tts_start) * 1000.0
        
        total_latency = (time.perf_counter() - total_start) * 1000.0

        metrics = PipelineTurnMetrics(
            stt_latency_ms=round(stt_latency, 2),
            llm_latency_ms=round(llm_latency, 2),
            tts_latency_ms=round(tts_latency, 2),
            total_latency_ms=round(total_latency, 2)
        )

        logger.info("Turn completed", extra=metrics.model_dump())

        return PipelineTurnResult(
            transcript=transcript,
            response_text=llm_result.content,
            audio_bytes=tts_result.audio_bytes,
            audio_format=tts_result.format,
            metrics=metrics
        )
