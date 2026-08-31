import asyncio
import struct
from typing import AsyncIterator, Optional
from app.voice.tts.base import BaseTTSProvider, TTSAudioResult

def create_mock_wav(duration_sec: float = 0.5, sample_rate: int = 24000) -> bytes:
    """
    Generate minimal valid silent WAV bytes for testing without external audio devices.
    """
    num_samples = int(duration_sec * sample_rate)
    byte_rate = sample_rate * 2 # 16-bit mono
    block_align = 2
    data_size = num_samples * 2
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,             # Subchunk1Size (16 for PCM)
        1,              # AudioFormat (1 for PCM)
        1,              # NumChannels (1 mono)
        sample_rate,    # SampleRate
        byte_rate,      # ByteRate
        block_align,    # BlockAlign
        16,             # BitsPerSample
        b'data',
        data_size
    )
    # Silent samples (0)
    data = b'\x00' * data_size
    return header + data

class MockTTSProvider(BaseTTSProvider):
    """
    Mock TTS Provider for simulation, local development, and test suites.
    """
    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> TTSAudioResult:
        await asyncio.sleep(0.05)
        audio = create_mock_wav(duration_sec=0.2 + len(text) * 0.01, sample_rate=self.sample_rate)
        return TTSAudioResult(
            audio_bytes=audio,
            sample_rate=self.sample_rate,
            format="wav"
        )

    async def stream_synthesize(self, text: str, voice_id: Optional[str] = None) -> AsyncIterator[bytes]:
        full_audio = await self.synthesize(text, voice_id)
        chunk_size = 1024
        for i in range(0, len(full_audio.audio_bytes), chunk_size):
            await asyncio.sleep(0.01)
            yield full_audio.audio_bytes[i:i + chunk_size]
