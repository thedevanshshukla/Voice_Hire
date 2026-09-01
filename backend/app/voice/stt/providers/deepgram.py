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
        if not audio_data or len(audio_data) < 100 or audio_data == b"\x00" * len(audio_data):
            return STTTranscriptionResult(
                text="",
                is_final=True,
                confidence=1.0,
                language=language
            )

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/octet-stream"
        }
        params = {
            "model": self.model,
            "language": language,
            "smart_format": "true",
            "punctuate": "true",
            "filler_words": "false",
            "keywords": [
                "SQL:3", "PostgreSQL:3", "MySQL:3", "Redis:3", "Kafka:3", "B-Tree:3", "MVCC:3",
                "deadlock:3", "concurrency:3", "mutex:3", "sharding:3", "replication:3",
                "latency:3", "throughput:3", "architecture:3", "Kubernetes:3", "Docker:3",
                "microservices:3", "REST:3", "GraphQL:3", "caching:3", "indexing:3",
                "optimistic locking:3", "pessimistic locking:3", "consistent hashing:3", "end:3"
            ]
        }
        try:
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
        except Exception as e:
            return STTTranscriptionResult(
                text="",
                is_final=True,
                confidence=0.0,
                language=language
            )

    async def stream_transcribe(self, audio_stream: AsyncIterator[bytes], language: str = "en") -> AsyncIterator[STTTranscriptionResult]:
        # For stream transcription, accumulates chunk buffer or connects to ws endpoint
        full_audio = bytearray()
        async for chunk in audio_stream:
            full_audio.extend(chunk)
            
        result = await self.transcribe(bytes(full_audio), language=language)
        yield result
