import time
from enum import Enum
from typing import Optional, Tuple
from pydantic import BaseModel, Field

from app.voice.vad.base import BaseVADProvider, VADFrameResult, VADState
from app.voice.vad.providers.energy import EnergyVADProvider
from app.config import settings
from app.core.logger import get_logger

logger = get_logger("voice.turn_detector")

class TurnStatus(str, Enum):
    IDLE = "idle"
    CANDIDATE_SPEAKING = "candidate_speaking"
    CANDIDATE_PAUSED = "candidate_paused"
    TURN_ENDPOINT = "turn_endpoint"

class TurnDetectionResult(BaseModel):
    status: TurnStatus
    is_turn_complete: bool = False
    speech_duration_ms: float = 0.0
    pause_duration_ms: float = 0.0
    pause_count: int = 0
    endpointing_delay_ms: float = 0.0

class TurnDetector:
    """
    Intelligent Turn Taking & Endpointing Engine.
    Distinguishes between short candidate pauses (thinking) and answer completion.
    """
    def __init__(
        self,
        vad_provider: Optional[BaseVADProvider] = None,
        silence_threshold_ms: int = 800,
        min_speech_duration_ms: int = 250,
        max_pause_tolerance_ms: int = 600
    ):
        self.vad = vad_provider or EnergyVADProvider()
        self.silence_threshold_ms = silence_threshold_ms
        self.min_speech_duration_ms = min_speech_duration_ms
        self.max_pause_tolerance_ms = max_pause_tolerance_ms

        self.status = TurnStatus.IDLE
        self.total_speech_ms: float = 0.0
        self.current_silence_ms: float = 0.0
        self.pause_count: int = 0
        self.turn_start_time: Optional[float] = None
        self.speech_end_time: Optional[float] = None

    def process_frame(self, audio_frame: bytes, sample_rate: int = 16000) -> TurnDetectionResult:
        vad_res: VADFrameResult = self.vad.process_frame(audio_frame, sample_rate)
        frame_duration_ms = (len(audio_frame) / 2 / sample_rate) * 1000.0 if sample_rate > 0 else 20.0

        if vad_res.is_speech:
            if self.status == TurnStatus.IDLE:
                self.turn_start_time = time.perf_counter()
                self.status = TurnStatus.CANDIDATE_SPEAKING
            elif self.status == TurnStatus.CANDIDATE_PAUSED:
                # Resumed speech after pause
                self.status = TurnStatus.CANDIDATE_SPEAKING

            self.total_speech_ms += frame_duration_ms
            self.current_silence_ms = 0.0
            self.speech_end_time = None

            return TurnDetectionResult(
                status=TurnStatus.CANDIDATE_SPEAKING,
                is_turn_complete=False,
                speech_duration_ms=round(self.total_speech_ms, 1),
                pause_duration_ms=0.0,
                pause_count=self.pause_count
            )

        else: # Silence frame
            if self.status in [TurnStatus.CANDIDATE_SPEAKING, TurnStatus.CANDIDATE_PAUSED]:
                if self.speech_end_time is None:
                    self.speech_end_time = time.perf_counter()
                    self.pause_count += 1

                self.current_silence_ms += frame_duration_ms

                # Check if total speech meets minimum threshold
                if self.total_speech_ms < self.min_speech_duration_ms:
                    # Ignore brief clicks/coughs as complete turns
                    if self.current_silence_ms > self.silence_threshold_ms:
                        self.reset()
                        return TurnDetectionResult(status=TurnStatus.IDLE, is_turn_complete=False)
                    return TurnDetectionResult(status=TurnStatus.IDLE, is_turn_complete=False)

                # Check if silence exceeded terminal threshold -> Answer is complete
                if self.current_silence_ms >= self.silence_threshold_ms:
                    endpointing_delay = self.current_silence_ms
                    self.status = TurnStatus.TURN_ENDPOINT
                    logger.info("Turn endpoint reached", extra={
                        "speech_ms": self.total_speech_ms,
                        "silence_ms": self.current_silence_ms,
                        "pause_count": self.pause_count,
                        "endpointing_delay_ms": round(endpointing_delay, 2)
                    })
                    return TurnDetectionResult(
                        status=TurnStatus.TURN_ENDPOINT,
                        is_turn_complete=True,
                        speech_duration_ms=round(self.total_speech_ms, 1),
                        pause_duration_ms=round(self.current_silence_ms, 1),
                        pause_count=self.pause_count,
                        endpointing_delay_ms=round(endpointing_delay, 1)
                    )
                else:
                    # Candidate is paused / thinking
                    self.status = TurnStatus.CANDIDATE_PAUSED
                    return TurnDetectionResult(
                        status=TurnStatus.CANDIDATE_PAUSED,
                        is_turn_complete=False,
                        speech_duration_ms=round(self.total_speech_ms, 1),
                        pause_duration_ms=round(self.current_silence_ms, 1),
                        pause_count=self.pause_count
                    )

            return TurnDetectionResult(
                status=TurnStatus.IDLE,
                is_turn_complete=False,
                speech_duration_ms=0.0,
                pause_duration_ms=round(self.current_silence_ms, 1),
                pause_count=self.pause_count
            )

    def reset(self):
        self.vad.reset()
        self.status = TurnStatus.IDLE
        self.total_speech_ms = 0.0
        self.current_silence_ms = 0.0
        self.pause_count = 0
        self.turn_start_time = None
        self.speech_end_time = None
