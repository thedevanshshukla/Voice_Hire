import asyncio
from typing import AsyncIterator
from app.voice.stt.base import BaseSTTProvider, STTTranscriptionResult

class MockSTTProvider(BaseSTTProvider):
    """
    Mock STT Provider for local development, simulation, and automated testing.
    """
    def __init__(self, default_response: str = "Hello, I am ready for the technical interview."):
        self.default_response = default_response

    async def transcribe(self, audio_data: bytes, language: str = "en") -> STTTranscriptionResult:
        # Simulate slight network/inference latency
        await asyncio.sleep(0.05)
        return STTTranscriptionResult(
            text=self.default_response,
            is_final=True,
            confidence=0.98,
            language=language
        )

    async def stream_transcribe(self, audio_stream: AsyncIterator[bytes], language: str = "en") -> AsyncIterator[STTTranscriptionResult]:
        words = self.default_response.split()
        partial = []
        for word in words:
            partial.append(word)
            await asyncio.sleep(0.02)
            yield STTTranscriptionResult(
                text=" ".join(partial),
                is_final=False,
                confidence=0.95,
                language=language
            )
        yield STTTranscriptionResult(
            text=self.default_response,
            is_final=True,
            confidence=0.99,
            language=language
        )
