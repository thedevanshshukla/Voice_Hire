import struct
import math
from typing import Optional
from app.voice.vad.base import BaseVADProvider, VADFrameResult, VADState

class EnergyVADProvider(BaseVADProvider):
    """
    Energy & RMS-based Voice Activity Detector with adaptive noise floor estimation.
    Zero external C/native dependency, ideal for robust cross-platform execution.
    """
    def __init__(
        self,
        energy_threshold: float = 0.015,
        noise_floor_alpha: float = 0.95
    ):
        self.energy_threshold = energy_threshold
        self.noise_floor_alpha = noise_floor_alpha
        self.noise_floor: float = 0.005
        
        self.speech_frames: int = 0
        self.silence_frames: int = 0
        self.current_state: VADState = VADState.SILENCE

    def calculate_rms(self, audio_frame: bytes) -> float:
        """Calculate Root Mean Square (RMS) amplitude of 16-bit PCM audio."""
        if not audio_frame or len(audio_frame) < 2:
            return 0.0
        
        num_samples = len(audio_frame) // 2
        try:
            # Unpack 16-bit signed little-endian integers
            samples = struct.unpack(f"<{num_samples}h", audio_frame[:num_samples * 2])
            sum_squares = sum(s * s for s in samples)
            mean_square = sum_squares / num_samples
            # Normalize to 0.0 - 1.0 (32768 is max int16)
            rms = math.sqrt(mean_square) / 32768.0
            return rms
        except Exception:
            return 0.0

    def process_frame(self, audio_frame: bytes, sample_rate: int = 16000) -> VADFrameResult:
        rms = self.calculate_rms(audio_frame)
        frame_duration_ms = (len(audio_frame) / 2 / sample_rate) * 1000.0 if sample_rate > 0 else 20.0
        
        # Adaptive noise floor update during silence
        if rms < self.noise_floor * 1.5:
            self.noise_floor = (self.noise_floor_alpha * self.noise_floor) + ((1 - self.noise_floor_alpha) * rms)
        
        effective_threshold = max(self.energy_threshold, self.noise_floor * 2.5)
        is_speech = rms > effective_threshold

        if is_speech:
            self.speech_frames += 1
            self.silence_frames = 0
            if self.speech_frames == 1:
                self.current_state = VADState.SPEECH_START
            else:
                self.current_state = VADState.SPEECH_ONGOING
        else:
            self.silence_frames += 1
            if self.speech_frames > 0:
                self.current_state = VADState.PAUSE
            else:
                self.current_state = VADState.SILENCE

        speech_ms = self.speech_frames * frame_duration_ms
        silence_ms = self.silence_frames * frame_duration_ms
        
        prob = min(1.0, max(0.0, (rms - self.noise_floor) / max(0.001, effective_threshold)))

        return VADFrameResult(
            is_speech=is_speech,
            probability=round(prob, 2),
            energy_level=round(rms, 4),
            state=self.current_state,
            speech_duration_ms=round(speech_ms, 1),
            silence_duration_ms=round(silence_ms, 1)
        )

    def reset(self):
        self.speech_frames = 0
        self.silence_frames = 0
        self.current_state = VADState.SILENCE
