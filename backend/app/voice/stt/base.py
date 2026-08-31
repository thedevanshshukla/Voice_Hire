from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel

class STTTranscriptionResult(BaseModel):
    text: str
    is_final: bool = True
    confidence: float = 1.0
    language: str = "en"

class BaseSTTProvider(ABC):
    """
    Abstract Base Class for Speech-to-Text (STT) Providers.
    """
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en") -> STTTranscriptionResult:
        """
        Transcribe raw audio bytes to text synchronously/single-shot.
        """
        pass

    @abstractmethod
    async def stream_transcribe(self, audio_stream: AsyncIterator[bytes], language: str = "en") -> AsyncIterator[STTTranscriptionResult]:
        """
        Stream audio bytes and yield partial and final transcription results.
        """
        pass
