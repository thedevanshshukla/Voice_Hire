import httpx
from typing import AsyncIterator, Optional
from app.voice.stt.base import BaseSTTProvider, STTTranscriptionResult

class DeepgramSTTProvider(BaseSTTProvider):
    """
    Deepgram Speech-to-Text Provider via Nova-2 REST / Streaming API.
    """
    def __init__(self, api_key: str, model: str = "nova-2"):
        if not api_key:
            raise ValueError("Deepgram API Key is required for DeepgramSTTProvider")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepgram.com/v1/listen"

    async def transcribe(self, audio_data: bytes, language: str = "en") -> STTTranscriptionResult:
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }
        params = {
            "model": self.model,
            "language": language,
            "smart_format": "true",
            "punctuate": "true"
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.base_url,
                params=params,
                headers=headers,
                content=audio_data
            )
            response.raise_for_status()
            data = response.json()
            
            transcript = ""
            confidence = 1.0
            results = data.get("results", {})
            channels = results.get("channels", [])
            if channels and len(channels) > 0:
                alternatives = channels[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].get("transcript", "")
                    confidence = alternatives[0].get("confidence", 1.0)
                    
            return STTTranscriptionResult(
                text=transcript,
                is_final=True,
                confidence=confidence,
                language=language
            )

    async def stream_transcribe(self, audio_stream: AsyncIterator[bytes], language: str = "en") -> AsyncIterator[STTTranscriptionResult]:
        # For stream transcription, accumulates chunk buffer or connects to ws endpoint
        full_audio = bytearray()
        async for chunk in audio_stream:
            full_audio.extend(chunk)
            
        result = await self.transcribe(bytes(full_audio), language=language)
        yield result
