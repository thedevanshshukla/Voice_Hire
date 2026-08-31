import httpx
from typing import AsyncIterator, Optional
from app.voice.tts.base import BaseTTSProvider, TTSAudioResult

class ElevenLabsTTSProvider(BaseTTSProvider):
    """
    ElevenLabs Text-to-Speech Provider.
    """
    def __init__(self, api_key: str, default_voice_id: str = "CwhRBWXzGAHq8TQ4Fs17", model_id: str = "eleven_turbo_v2_5"):
        if not api_key:
            raise ValueError("ElevenLabs API Key is required for ElevenLabsTTSProvider")
        self.api_key = api_key
        self.default_voice_id = default_voice_id
        self.model_id = model_id
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSAudioResult:
        vid = voice_id or self.default_voice_id
        url = f"{self.base_url}/{vid}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            return TTSAudioResult(
                audio_bytes=res.content,
                sample_rate=24000,
                format="mp3"
            )

    async def stream_synthesize(self, text: str, voice_id: Optional[str] = None) -> AsyncIterator[bytes]:
        vid = voice_id or self.default_voice_id
        url = f"{self.base_url}/{vid}/stream"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": self.model_id
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
