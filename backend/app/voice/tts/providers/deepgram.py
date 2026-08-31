import httpx
from typing import AsyncIterator, Optional
from app.voice.tts.base import BaseTTSProvider, TTSAudioResult

class DeepgramTTSProvider(BaseTTSProvider):
    """
    Deepgram Aura Text-to-Speech Provider.
    """
    def __init__(self, api_key: str, model: str = "aura-asteria-en"):
        if not api_key:
            raise ValueError("Deepgram API Key is required for DeepgramTTSProvider")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepgram.com/v1/speak"

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSAudioResult:
        model_name = voice_id or self.model
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {"model": model_name}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(self.base_url, params=params, headers=headers, json={"text": text})
            res.raise_for_status()
            return TTSAudioResult(
                audio_bytes=res.content,
                sample_rate=24000,
                format="mp3"
            )

    async def stream_synthesize(self, text: str, voice_id: Optional[str] = None) -> AsyncIterator[bytes]:
        model_name = voice_id or self.model
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {"model": model_name}
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", self.base_url, params=params, headers=headers, json={"text": text}) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
