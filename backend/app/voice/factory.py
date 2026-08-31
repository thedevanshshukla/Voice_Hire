from typing import Optional
from app.config import settings
from app.voice.stt.base import BaseSTTProvider
from app.voice.stt.providers.mock import MockSTTProvider
from app.voice.stt.providers.deepgram import DeepgramSTTProvider

from app.voice.llm.base import BaseLLMProvider
from app.voice.llm.providers.mock import MockLLMProvider
from app.voice.llm.providers.openai import OpenAILLMProvider
from app.voice.llm.providers.gemini import GeminiLLMProvider

from app.voice.tts.base import BaseTTSProvider
from app.voice.tts.providers.mock import MockTTSProvider
from app.voice.tts.providers.elevenlabs import ElevenLabsTTSProvider
from app.voice.tts.providers.deepgram import DeepgramTTSProvider

class VoiceProviderFactory:
    """
    Factory for instantiating STT, LLM, and TTS providers based on system configuration or overrides.
    """
    
    @staticmethod
    def get_stt_provider(provider_name: Optional[str] = None) -> BaseSTTProvider:
        name = (provider_name or settings.STT_PROVIDER).lower()
        if name == "deepgram":
            if not settings.DEEPGRAM_API_KEY:
                return MockSTTProvider(default_response="Deepgram API key not provided; fallback mock response.")
            return DeepgramSTTProvider(api_key=settings.DEEPGRAM_API_KEY)
        return MockSTTProvider()

    @staticmethod
    def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
        name = (provider_name or settings.LLM_PROVIDER).lower()
        if name == "openai":
            if not settings.OPENAI_API_KEY:
                return MockLLMProvider(default_reply="OpenAI API key not set; fallback mock response.")
            return OpenAILLMProvider(api_key=settings.OPENAI_API_KEY)
        elif name == "gemini":
            if not settings.GEMINI_API_KEY:
                return MockLLMProvider(default_reply="Gemini API key not set; fallback mock response.")
            return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY)
        return MockLLMProvider()

    @staticmethod
    def get_tts_provider(provider_name: Optional[str] = None) -> BaseTTSProvider:
        name = (provider_name or settings.TTS_PROVIDER).lower()
        if name == "elevenlabs":
            if not settings.ELEVEN_LABS_API_KEY:
                return MockTTSProvider()
            return ElevenLabsTTSProvider(api_key=settings.ELEVEN_LABS_API_KEY)
        elif name == "deepgram":
            if not settings.DEEPGRAM_API_KEY:
                return MockTTSProvider()
            return DeepgramTTSProvider(api_key=settings.DEEPGRAM_API_KEY)
        return MockTTSProvider()
