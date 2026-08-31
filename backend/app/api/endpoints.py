import base64
import json
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.logger import get_logger
from app.agent.worker import generate_livekit_token
from app.voice.factory import VoiceProviderFactory
from app.voice.pipeline import BasicVoicePipeline, PipelineTurnResult
from app.voice.streaming_pipeline import StreamingVoicePipeline, StreamAudioEvent
from app.voice.vad.turn_detector import TurnDetector, TurnDetectionResult
from app.voice.vad.providers.energy import EnergyVADProvider
from app.voice.llm.base import LLMMessage

logger = get_logger("api.endpoints")
router = APIRouter()

# Global pipeline instances
voice_pipeline = BasicVoicePipeline()
streaming_pipeline = StreamingVoicePipeline()
turn_detector = TurnDetector()

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
    metrics: Dict[str, Any]

class VADFrameRequest(BaseModel):
    audio_frame_b64: str
    sample_rate: int = 16000

class VADFrameResponse(BaseModel):
    status: str
    is_turn_complete: bool
    speech_duration_ms: float
    pause_duration_ms: float
    pause_count: int

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
            "tts": settings.TTS_PROVIDER,
            "vad": settings.VAD_PROVIDER
        }
    }

@router.get("/api/voice/status")
async def voice_status() -> Dict[str, Any]:
    """
    Returns the configured voice providers, LiveKit status, streaming, and VAD settings.
    """
    return {
        "livekit_url": settings.LIVEKIT_URL,
        "providers": {
            "stt": settings.STT_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "tts": settings.TTS_PROVIDER,
            "vad": settings.VAD_PROVIDER
        },
        "vad_settings": {
            "silence_threshold_ms": settings.VAD_SILENCE_THRESHOLD_MS,
            "min_speech_ms": settings.VAD_MIN_SPEECH_DURATION_MS,
            "pause_tolerance_ms": settings.VAD_MAX_PAUSE_TOLERANCE_MS
        },
        "streaming_supported": True,
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

@router.post("/api/voice/vad/process", response_model=VADFrameResponse)
async def process_vad_frame(req: VADFrameRequest) -> VADFrameResponse:
    """
    Process incoming audio frame through TurnDetector and return activity state.
    """
    try:
        frame_bytes = base64.b64decode(req.audio_frame_b64)
        res: TurnDetectionResult = turn_detector.process_frame(frame_bytes, sample_rate=req.sample_rate)
        return VADFrameResponse(
            status=res.status.value,
            is_turn_complete=res.is_turn_complete,
            speech_duration_ms=res.speech_duration_ms,
            pause_duration_ms=res.pause_duration_ms,
            pause_count=res.pause_count
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"VAD frame processing failed: {str(e)}")

@router.post("/api/voice/turn", response_model=VoiceTurnResponse)
async def process_voice_turn(req: VoiceTurnRequest) -> VoiceTurnResponse:
    """
    Process a single voice turn with roundtrip latency diagnostics.
    """
    try:
        if req.audio_base64:
            audio_bytes = base64.b64decode(req.audio_base64)
        else:
            audio_bytes = b"\x00" * 3200

        history_msgs = []
        if req.history:
            for item in req.history:
                history_msgs.append(LLMMessage(role=item.get("role", "user"), content=item.get("content", "")))

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

@router.websocket("/api/voice/stream/ws")
async def voice_streaming_websocket(websocket: WebSocket):
    """
    Full-duplex WebSocket endpoint for real-time streaming voice sessions with VAD events.
    """
    await websocket.accept()
    logger.info("WebSocket voice stream client connected")
    
    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            
            action = data.get("action", "turn")
            text = data.get("text")
            audio_b64 = data.get("audio_base64")
            history = data.get("history", [])
            
            history_msgs = [
                LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
                for m in history
            ]
            
            raw_audio = base64.b64decode(audio_b64) if audio_b64 else None
            
            # Execute streaming turn
            async for event in streaming_pipeline.stream_turn(
                input_text=text,
                raw_audio=raw_audio,
                history=history_msgs
            ):
                payload = {
                    "event_type": event.event_type,
                    "vad_status": event.vad_status,
                    "text": event.text,
                    "audio_format": event.audio_format
                }
                if event.audio_bytes:
                    payload["audio_chunk_b64"] = base64.b64encode(event.audio_bytes).decode("utf-8")
                if event.metrics:
                    payload["metrics"] = event.metrics.model_dump()
                    
                await websocket.send_json(payload)
                
    except WebSocketDisconnect:
        logger.info("WebSocket voice stream client disconnected")
    except Exception as e:
        logger.error("WebSocket stream error", extra={"error": str(e)})
        try:
            await websocket.send_json({"event_type": "error", "message": str(e)})
        except Exception:
            pass
