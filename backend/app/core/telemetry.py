import time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.logger import get_logger

logger = get_logger("telemetry.latency")

class TurnLatencyMetrics(BaseModel):
    stt_latency_ms: float = Field(0.0, description="Time taken to transcribe speech to text")
    llm_ttft_ms: float = Field(0.0, description="Time to First Token (TTFT) from LLM generation start")
    llm_total_ms: float = Field(0.0, description="Total duration of LLM token generation")
    tts_ttfa_ms: float = Field(0.0, description="Time to First Audio (TTFA) chunk synthesized")
    tts_total_ms: float = Field(0.0, description="Total duration of TTS audio generation")
    
    # Natural Turn Taking Metrics (v0.4.0)
    speech_duration_ms: float = Field(0.0, description="Total duration of active candidate speech")
    pause_count: int = Field(0, description="Number of intra-turn thinking pauses detected")
    endpointing_delay_ms: float = Field(0.0, description="Duration of terminal silence before taking turn")
    
    total_perceived_ms: float = Field(0.0, description="Perceived latency: Speech end to first audio playback")
    total_turn_ms: float = Field(0.0, description="Total roundtrip duration of the turn")

class StreamingMetricsTracker:
    """
    Precision latency tracker for streaming Voice AI pipelines.
    Tracks Time-to-First-Token (TTFT), Time-to-First-Audio (TTFA), VAD endpointing, and total turnaround.
    """
    def __init__(self):
        self.turn_start_time: float = time.perf_counter()
        self.stt_start_time: Optional[float] = None
        self.stt_end_time: Optional[float] = None
        
        self.llm_start_time: Optional[float] = None
        self.llm_first_token_time: Optional[float] = None
        self.llm_end_time: Optional[float] = None
        
        self.tts_start_time: Optional[float] = None
        self.tts_first_audio_time: Optional[float] = None
        self.tts_end_time: Optional[float] = None

        # Turn Taking Metrics
        self.speech_duration_ms: float = 0.0
        self.pause_count: int = 0
        self.endpointing_delay_ms: float = 0.0

    def set_turn_vad_metrics(self, speech_ms: float, pause_count: int, endpointing_ms: float):
        self.speech_duration_ms = speech_ms
        self.pause_count = pause_count
        self.endpointing_delay_ms = endpointing_ms

    def mark_stt_start(self):
        self.stt_start_time = time.perf_counter()

    def mark_stt_end(self):
        self.stt_end_time = time.perf_counter()

    def mark_llm_start(self):
        self.llm_start_time = time.perf_counter()

    def mark_llm_first_token(self):
        if self.llm_first_token_time is None:
            self.llm_first_token_time = time.perf_counter()

    def mark_llm_end(self):
        self.llm_end_time = time.perf_counter()

    def mark_tts_start(self):
        if self.tts_start_time is None:
            self.tts_start_time = time.perf_counter()

    def mark_tts_first_audio(self):
        if self.tts_first_audio_time is None:
            self.tts_first_audio_time = time.perf_counter()

    def mark_tts_end(self):
        self.tts_end_time = time.perf_counter()

    def compute_metrics(self) -> TurnLatencyMetrics:
        now = time.perf_counter()
        
        # STT Latency
        stt_ms = 0.0
        if self.stt_start_time and self.stt_end_time:
            stt_ms = (self.stt_end_time - self.stt_start_time) * 1000.0
            
        # LLM TTFT
        llm_ttft_ms = 0.0
        if self.llm_start_time and self.llm_first_token_time:
            llm_ttft_ms = (self.llm_first_token_time - self.llm_start_time) * 1000.0

        # LLM Total
        llm_total_ms = 0.0
        if self.llm_start_time and self.llm_end_time:
            llm_total_ms = (self.llm_end_time - self.llm_start_time) * 1000.0

        # TTS TTFA
        tts_ttfa_ms = 0.0
        if self.tts_start_time and self.tts_first_audio_time:
            tts_ttfa_ms = (self.tts_first_audio_time - self.tts_start_time) * 1000.0

        # TTS Total
        tts_total_ms = 0.0
        if self.tts_start_time and self.tts_end_time:
            tts_total_ms = (self.tts_end_time - self.tts_start_time) * 1000.0

        # Perceived latency: Turn start to first audio chunk ready
        first_audio_point = self.tts_first_audio_time or now
        perceived_ms = (first_audio_point - self.turn_start_time) * 1000.0
        
        # Total roundtrip
        total_ms = (now - self.turn_start_time) * 1000.0

        metrics = TurnLatencyMetrics(
            stt_latency_ms=round(stt_ms, 2),
            llm_ttft_ms=round(llm_ttft_ms, 2),
            llm_total_ms=round(llm_total_ms, 2),
            tts_ttfa_ms=round(tts_ttfa_ms, 2),
            tts_total_ms=round(tts_total_ms, 2),
            speech_duration_ms=round(self.speech_duration_ms, 2),
            pause_count=self.pause_count,
            endpointing_delay_ms=round(self.endpointing_delay_ms, 2),
            total_perceived_ms=round(perceived_ms, 2),
            total_turn_ms=round(total_ms, 2)
        )
        
        logger.info("Turn Telemetry", extra=metrics.model_dump())
        return metrics
