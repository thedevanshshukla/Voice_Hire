import base64
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.logger import get_logger
from app.agent.worker import generate_livekit_token
from app.voice.factory import VoiceProviderFactory
from app.voice.pipeline import BasicVoicePipeline, PipelineTurnResult
from app.voice.llm.base import LLMMessage

logger = get_logger("api.endpoints")
router = APIRouter()

# Global pipeline instance for API requests
voice_pipeline = BasicVoicePipeline()

class TokenRequest(BaseModel):
    room_name: str = Field(..., description="Unique LiveKit room name")
    identity: str = Field(..., description="Unique participant identity (e.g. candidate-123)")
    name: Optional[str] = Field(None, description="Display name of candidate")

class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    identity: str

class VoiceTurnRequest(BaseModel):
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio bytes (optional if text is provided)")
    text: Optional[str] = Field(None, description="Direct text input for testing pipeline")
    language: str = "en"
    history: Optional[List[Dict[str, str]]] = None

class VoiceTurnResponse(BaseModel):
    transcript: str
    response_text: str
    audio_base64: str
    audio_format: str
    metrics: Dict[str, float]

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify backend status, version, and provider configuration.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "version": settings.VERSION,
        "providers": {
            "stt": settings.STT_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "tts": settings.TTS_PROVIDER
        }
    }

@router.get("/api/voice/status")
async def voice_status() -> Dict[str, Any]:
    """
    Returns the configured voice providers and LiveKit connection status.
    """
    return {
        "livekit_url": settings.LIVEKIT_URL,
        "providers": {
            "stt": settings.STT_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "tts": settings.TTS_PROVIDER
        },
        "version": settings.VERSION
    }

@router.post("/api/voice/token", response_model=TokenResponse)
async def get_voice_token(req: TokenRequest) -> TokenResponse:
    """
    Generate a signed LiveKit WebRTC participant token for joining an interview voice session.
    """
    try:
        token = generate_livekit_token(
            room_name=req.room_name,
            identity=req.identity,
            name=req.name
        )
        return TokenResponse(
            token=token,
            url=settings.LIVEKIT_URL,
            room_name=req.room_name,
            identity=req.identity
        )
    except Exception as e:
        logger.error("Failed to generate token", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}"
        )

@router.post("/api/voice/turn", response_model=VoiceTurnResponse)
async def process_voice_turn(req: VoiceTurnRequest) -> VoiceTurnResponse:
    """
    Process a single voice turn (Audio In -> STT -> LLM -> TTS -> Audio Out) with latency diagnostics.
    """
    try:
        # Decode audio or create placeholder bytes
        if req.audio_base64:
            audio_bytes = base64.b64decode(req.audio_base64)
        else:
            # Generate empty audio bytes for text simulation
            audio_bytes = b"\x00" * 3200

        # Build message history
        history_msgs = []
        if req.history:
            for item in req.history:
                history_msgs.append(LLMMessage(role=item.get("role", "user"), content=item.get("content", "")))

        # Override mock STT if text was explicitly sent in test mode
        if req.text and isinstance(voice_pipeline.stt, type(VoiceProviderFactory.get_stt_provider("mock"))):
            voice_pipeline.stt.default_response = req.text

        turn_result: PipelineTurnResult = await voice_pipeline.process_turn(
            audio_in=audio_bytes,
            history=history_msgs,
            language=req.language
        )

        return VoiceTurnResponse(
            transcript=turn_result.transcript,
            response_text=turn_result.response_text,
            audio_base64=base64.b64encode(turn_result.audio_bytes).decode("utf-8"),
            audio_format=turn_result.audio_format,
            metrics=turn_result.metrics.model_dump()
        )
    except Exception as e:
        logger.error("Turn processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Turn processing failed: {str(e)}"
        )
