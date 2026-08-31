from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel

class TTSAudioResult(BaseModel):
    audio_bytes: bytes
    sample_rate: int = 24000
    format: str = "wav" # wav, mp3, pcm

class BaseTTSProvider(ABC):
    """
    Abstract Base Class for Text-to-Speech (TTS) Providers.
    """
    
    @abstractmethod
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSAudioResult:
        """
        Synthesize text into complete audio bytes.
        """
        pass

    @abstractmethod
    async def stream_synthesize(self, text: str, voice_id: Optional[str] = None) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio chunks.
        """
        pass
