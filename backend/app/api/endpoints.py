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
from app.voice.interruption.cancellation import CancellationToken
from app.voice.interruption.barge_in import BargeInDetector
from app.voice.llm.base import LLMMessage
from app.models.interview import (
    InterviewSession, InterviewConfig, InterviewRole, ExperienceLevel,
    InterviewLanguage, InterviewTopic, TranscriptEntry, SessionStatus
)
from app.db.mongo import InterviewSessionRepository
from app.interview.prompt_builder import InterviewPromptBuilder

logger = get_logger("api.endpoints")
router = APIRouter()

# Global pipeline instances
voice_pipeline = BasicVoicePipeline()
streaming_pipeline = StreamingVoicePipeline()
turn_detector = TurnDetector()
barge_in_detector = BargeInDetector()

class TokenRequest(BaseModel):
    room_name: str = Field(..., description="Unique LiveKit room name")
    identity: str = Field(..., description="Unique participant identity (e.g. candidate-123)")
    name: Optional[str] = Field(None, description="Display name of candidate")
    session_id: Optional[str] = Field(None, description="Associated interview session ID")

class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    identity: str
    session_id: Optional[str] = None

class VoiceTurnRequest(BaseModel):
    session_id: Optional[str] = None
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

# ==========================================
# 1. Interview Configuration & Session APIs
# ==========================================

@router.get("/api/interview/templates")
async def get_interview_templates() -> Dict[str, Any]:
    """
    Returns available roles, experience levels, default topics, and supported languages.
    """
    return {
        "roles": [r.value for r in InterviewRole],
        "experience_levels": [e.value for e in ExperienceLevel],
        "topics": [t.value for t in InterviewTopic],
        "languages": [l.value for l in InterviewLanguage],
        "default_duration_minutes": 30
    }

@router.post("/api/interview/session", response_model=InterviewSession)
async def create_interview_session(config: InterviewConfig, candidate_name: str = "Candidate") -> InterviewSession:
    """
    Create and persist a new technical interview session with role, level, topics, and JD in MongoDB.
    """
    session = InterviewSession(
        candidate_name=candidate_name,
        config=config,
        status=SessionStatus.CONFIGURED
    )
    return await InterviewSessionRepository.create_session(session)

@router.get("/api/interview/session/{session_id}", response_model=InterviewSession)
async def get_interview_session(session_id: str) -> InterviewSession:
    """
    Retrieve interview session details and transcript history from MongoDB.
    """
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.get("/api/interview/sessions", response_model=List[InterviewSession])
async def list_interview_sessions(candidate_id: Optional[str] = None, limit: int = 20) -> List[InterviewSession]:
    """
    List previous interview sessions from MongoDB.
    """
    return await InterviewSessionRepository.list_sessions(candidate_id=candidate_id, limit=limit)

# ==========================================
# 2. System Diagnostics & Health
# ==========================================

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
        },
        "features": {
            "streaming": True,
            "barge_in": settings.BARGE_IN_ENABLED,
            "interview_foundation": True
        }
    }

@router.get("/api/voice/status")
async def voice_status() -> Dict[str, Any]:
    """
    Returns configured voice providers, LiveKit status, streaming, VAD, and interview configurations.
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
        "barge_in_settings": {
            "enabled": settings.BARGE_IN_ENABLED,
            "min_speech_ms": settings.BARGE_IN_MIN_SPEECH_MS,
            "energy_threshold": settings.BARGE_IN_ENERGY_THRESHOLD
        },
        "streaming_supported": True,
        "version": settings.VERSION
    }

# ==========================================
# 3. Voice Token & Turn Endpoints
# ==========================================

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
            identity=req.identity,
            session_id=req.session_id
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
    Process a single voice turn with contextual system prompt generation and transcript persistence.
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

        # Retrieve session context if session_id provided
        system_prompt = None
        session = None
        if req.session_id:
            session = await InterviewSessionRepository.get_session(req.session_id)
            if session:
                system_prompt = InterviewPromptBuilder.build_system_prompt(session.config, session.candidate_name)

        if req.text and isinstance(voice_pipeline.stt, type(VoiceProviderFactory.get_stt_provider("mock"))):
            voice_pipeline.stt.default_response = req.text

        turn_result: PipelineTurnResult = await voice_pipeline.process_turn(
            audio_in=audio_bytes,
            history=history_msgs,
            system_prompt=system_prompt,
            language=req.language
        )

        # Persist transcripts to session if active
        if session:
            session.transcripts.append(TranscriptEntry(role="candidate", text=turn_result.transcript))
            session.transcripts.append(TranscriptEntry(role="interviewer", text=turn_result.response_text, metrics=turn_result.metrics.model_dump()))
            session.turn_count += 1
            await InterviewSessionRepository.update_session(session.session_id, {
                "transcripts": [t.model_dump() for t in session.transcripts],
                "turn_count": session.turn_count
            })

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
    Full-duplex WebSocket endpoint for real-time streaming voice sessions with Interview Context and Barge-In.
    """
    await websocket.accept()
    logger.info("WebSocket voice stream client connected")
    
    current_token: Optional[CancellationToken] = None
    
    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            
            action = data.get("action", "turn")
            
            if action == "interrupt":
                if current_token and not current_token.is_cancelled:
                    current_token.cancel(reason=data.get("reason", "client_interrupt"))
                    await websocket.send_json({
                        "event_type": "interrupted",
                        "cancellation_latency_ms": current_token.cancellation_latency_ms
                    })
                continue

            text = data.get("text")
            audio_b64 = data.get("audio_base64")
            session_id = data.get("session_id")
            history = data.get("history", [])
            
            # Fetch contextual system prompt
            system_prompt = None
            if session_id:
                session = await InterviewSessionRepository.get_session(session_id)
                if session:
                    system_prompt = InterviewPromptBuilder.build_system_prompt(session.config, session.candidate_name)

            history_msgs = [
                LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
                for m in history
            ]
            
            raw_audio = base64.b64decode(audio_b64) if audio_b64 else None
            current_token = CancellationToken()
            
            # Execute streaming turn with contextual prompt and cancellation token
            async for event in streaming_pipeline.stream_turn(
                input_text=text,
                raw_audio=raw_audio,
                history=history_msgs,
                system_prompt=system_prompt,
                cancellation_token=current_token
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
        if current_token and not current_token.is_cancelled:
            current_token.cancel("client_disconnect")
    except Exception as e:
        logger.error("WebSocket stream error", extra={"error": str(e)})
        try:
            await websocket.send_json({"event_type": "error", "message": str(e)})
        except Exception:
            pass
