import time
from typing import Optional
from pydantic import BaseModel, Field
from app.voice.vad.base import BaseVADProvider, VADFrameResult
from app.voice.vad.providers.energy import EnergyVADProvider
from app.voice.interruption.cancellation import CancellationToken
from app.core.logger import get_logger

logger = get_logger("voice.barge_in")

class BargeInResult(BaseModel):
    is_interrupted: bool = False
    speech_duration_ms: float = 0.0
    detection_latency_ms: float = 0.0
    reason: Optional[str] = None

class BargeInDetector:
    """
    Real-time Barge-In & Interruption Detection Engine.
    Detects candidate speech during AI output and immediately halts active audio generation.
    """
    def __init__(
        self,
        vad_provider: Optional[BaseVADProvider] = None,
        min_speech_duration_ms: int = 120,
        energy_threshold: float = 0.02
    ):
        self.vad = vad_provider or EnergyVADProvider(energy_threshold=energy_threshold)
        self.min_speech_duration_ms = min_speech_duration_ms
        
        self.is_agent_active: bool = False
        self.consecutive_speech_frames: int = 0
        self.interruption_start_time: Optional[float] = None
        self.interruption_count: int = 0

    def set_agent_state(self, is_active: bool):
        """Update whether the agent is currently speaking or generating."""
        self.is_agent_active = is_active
        if not is_active:
            self.consecutive_speech_frames = 0
            self.interruption_start_time = None

    def process_frame(
        self, 
        audio_frame: bytes, 
        cancellation_token: Optional[CancellationToken] = None,
        sample_rate: int = 16000
    ) -> BargeInResult:
        if not self.is_agent_active:
            return BargeInResult(is_interrupted=False)

        vad_res: VADFrameResult = self.vad.process_frame(audio_frame, sample_rate)
        frame_duration_ms = (len(audio_frame) / 2 / sample_rate) * 1000.0 if sample_rate > 0 else 20.0

        if vad_res.is_speech:
            if self.interruption_start_time is None:
                self.interruption_start_time = time.perf_counter()

            self.consecutive_speech_frames += 1
            speech_ms = self.consecutive_speech_frames * frame_duration_ms

            if speech_ms >= self.min_speech_duration_ms:
                detection_latency = (time.perf_counter() - self.interruption_start_time) * 1000.0
                self.interruption_count += 1
                
                logger.info("Barge-in detected: cancelling active agent output", extra={
                    "speech_ms": speech_ms,
                    "detection_latency_ms": round(detection_latency, 2),
                    "total_interruptions": self.interruption_count
                })

                if cancellation_token and not cancellation_token.is_cancelled:
                    cancellation_token.cancel(reason="candidate_barge_in")

                self.is_agent_active = False
                self.consecutive_speech_frames = 0

                return BargeInResult(
                    is_interrupted=True,
                    speech_duration_ms=round(speech_ms, 1),
                    detection_latency_ms=round(detection_latency, 1),
                    reason="candidate_barge_in"
                )
        else:
            # Reset frame accumulator if speech stopped
            self.consecutive_speech_frames = 0
            self.interruption_start_time = None

        return BargeInResult(is_interrupted=False)

    def reset(self):
        self.vad.reset()
        self.is_agent_active = False
        self.consecutive_speech_frames = 0
        self.interruption_start_time = None
        self.interruption_count = 0
