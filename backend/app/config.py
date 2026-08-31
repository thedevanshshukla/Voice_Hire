from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "VoiceHire"
    VERSION: str = "0.13.0"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # LiveKit Settings
    LIVEKIT_URL: str = Field(default="ws://localhost:7880", description="LiveKit server WebSocket URL")
    LIVEKIT_API_KEY: str = Field(default="devkey", description="LiveKit API Key")
    LIVEKIT_API_SECRET: str = Field(default="secret", description="LiveKit API Secret")
    
    # Provider Settings (STT / LLM / TTS)
    STT_PROVIDER: str = Field(default="mock", description="Default STT provider: mock, deepgram")
    LLM_PROVIDER: str = Field(default="mock", description="Default LLM provider: mock, openai, gemini")
    TTS_PROVIDER: str = Field(default="mock", description="Default TTS provider: mock, elevenlabs, deepgram")
    
    # VAD & Turn Taking Settings
    VAD_PROVIDER: str = Field(default="energy", description="Default VAD provider: energy, mock")
    VAD_SILENCE_THRESHOLD_MS: int = Field(default=800, description="Silence duration in ms before endpointing turn")
    VAD_MIN_SPEECH_DURATION_MS: int = Field(default=250, description="Minimum speech duration to register turn")
    VAD_MAX_PAUSE_TOLERANCE_MS: int = Field(default=600, description="Pause duration tolerated before evaluating endpoint")
    
    # Barge-In / Interruption Settings
    BARGE_IN_ENABLED: bool = Field(default=True, description="Enable natural interruption / barge-in")
    BARGE_IN_MIN_SPEECH_MS: int = Field(default=120, description="Minimum speech duration during agent turn to trigger barge-in")
    BARGE_IN_ENERGY_THRESHOLD: float = Field(default=0.02, description="Energy threshold for interruption detection")
    
    # API Keys for Cloud Providers
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    ELEVEN_LABS_API_KEY: Optional[str] = None
    
    # Database
    MONGODB_URI: str = "mongodb://localhost:27017/voicehire"
    MONGODB_DB_NAME: str = "voicehire"
    
    # Config configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
