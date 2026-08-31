from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class VADState(str, Enum):
    SILENCE = "silence"
    SPEECH_START = "speech_start"
    SPEECH_ONGOING = "speech_ongoing"
    PAUSE = "pause"
    SPEECH_END = "speech_end"

class VADFrameResult(BaseModel):
    is_speech: bool
    probability: float = 1.0
    energy_level: float = 0.0
    state: VADState = VADState.SILENCE
    speech_duration_ms: float = 0.0
    silence_duration_ms: float = 0.0

class BaseVADProvider(ABC):
    """
    Abstract Base Class for Voice Activity Detection (VAD) Providers.
    """
    @abstractmethod
    def process_frame(self, audio_frame: bytes, sample_rate: int = 16000) -> VADFrameResult:
        """
        Process a single audio frame (e.g. 10ms-30ms raw PCM16 bytes) and return activity state.
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Reset internal state buffers.
        """
        pass
