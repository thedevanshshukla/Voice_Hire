import base64
import json
import re
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status, Response, Request
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
from app.voice.multilingual import LanguageDetector
from app.voice.llm.base import LLMMessage
from app.models.interview import (
    InterviewSession, InterviewConfig, InterviewRole, ExperienceLevel,
    InterviewLanguage, InterviewTopic, InterviewStage, TranscriptEntry,
    SessionStatus, TurnEvaluation, SessionScorecard, EvidenceEvaluationReport,
    ShortTermMemory, ContradictionItem, CandidateProfile
)
from app.models.knowledge import KnowledgeDocument, KnowledgeCategory, KnowledgeSearchResult
from app.models.tools import (
    ToolResult, ArchitectureDiagramPayload, CodeExecutionPayload,
    DocumentationLookupPayload, HumanFlagPayload, ExecuteToolRequest
)
from app.models.experiments import ExperimentConfig, ExperimentResult
from app.models.benchmark import BenchmarkRunSummary
from app.models.scale import LoadTestConfig, LoadTestResult
from app.models.user import User, SignupRequest, LoginRequest, AuthResponse, UserProfile
from app.auth.security import hash_password, verify_password, create_access_token, verify_access_token
from app.db.mongo import InterviewSessionRepository, UserRepository
from app.interview.prompt_builder import InterviewPromptBuilder
from app.interview.state_machine import InterviewStateMachine, STAGE_SEQUENCE, STAGE_DISPLAY_NAMES
from app.interview.adaptive_engine import AdaptiveQuestionEngine, AdaptiveAction
from app.interview.evaluation_engine import AnswerEvaluator
from app.interview.evidence_engine import EvidenceEvaluator
from app.interview.memory_engine import InterviewMemoryEngine, CandidateProfileRepository
from app.knowledge.rag_engine import KnowledgeRAGEngine
from app.agent.tools.executor import AgentToolExecutor
from app.observability.telemetry import TurnSpan, MetricsExporter
from app.experiments.ab_engine import ABExperimentManager
from app.evaluation.benchmark_runner import BenchmarkRunner
from app.security.sanitizer import PIISanitizer, SlidingWindowRateLimiter
from app.scale.load_runner import ConcurrentLoadSimulator

logger = get_logger("api.endpoints")
router = APIRouter()

# Global pipeline instances
voice_pipeline = BasicVoicePipeline()
streaming_pipeline = StreamingVoicePipeline()
turn_detector = TurnDetector()
barge_in_detector = BargeInDetector()
rag_engine = KnowledgeRAGEngine()

# In-memory active session state machines, adaptive engines, memory & language state
active_state_machines: Dict[str, InterviewStateMachine] = {}
active_adaptive_engines: Dict[str, AdaptiveQuestionEngine] = {}
active_memory_engines: Dict[str, InterviewMemoryEngine] = {}
active_diagrams: Dict[str, ArchitectureDiagramPayload] = {}
active_languages: Dict[str, InterviewLanguage] = {}

class TokenRequest(BaseModel):
    room_name: str = Field(..., description="Unique LiveKit room name")
    identity: str = Field(..., description="Unique participant identity (e.g. candidate-123)")
    name: Optional[str] = Field(None, description="Display name of candidate")
    session_id: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    identity: str
    session_id: Optional[str] = None

class DetectLanguageRequest(BaseModel):
    text: str

class DetectLanguageResponse(BaseModel):
    detected_language: str
    confidence: float

class CreateSessionRequest(BaseModel):
    candidate_name: str = Field(default="Candidate")
    user_email: Optional[str] = None
    config: InterviewConfig

class VoiceTurnRequest(BaseModel):
    session_id: Optional[str] = None
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio bytes (optional if text is provided)")
    text: Optional[str] = Field(None, description="Direct text input for testing pipeline")
    language: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class VoiceTurnResponse(BaseModel):
    transcript: str
    response_text: str
    audio_base64: str
    audio_format: str
    current_stage: str
    stage_display_name: str
    progress_pct: float
    detected_language: str = "English"
    adaptive_strategy: Optional[str] = None
    evaluated_depth: Optional[str] = None
    turn_evaluation: Optional[TurnEvaluation] = None
    scorecard: Optional[SessionScorecard] = None
    evidence_report: Optional[EvidenceEvaluationReport] = None
    rag_snippet: Optional[str] = None
    memory_claims_count: int = 0
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    active_diagram: Optional[ArchitectureDiagramPayload] = None
    topic_coverage: Optional[Dict[str, Any]] = None
    assigned_variants: Optional[Dict[str, str]] = None
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

class SearchKnowledgeRequest(BaseModel):
    query: str
    role_target: Optional[str] = None
    top_k: int = 2

# ==========================================
# 0. User Authentication & Profile APIs
# ==========================================

@router.post("/api/auth/signup", response_model=AuthResponse)
async def signup_user(req: SignupRequest) -> AuthResponse:
    existing = await UserRepository.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    
    import uuid
    new_user = User(
        user_id=f"user-{uuid.uuid4().hex[:8]}",
        email=req.email.lower().strip(),
        full_name=req.full_name.strip(),
        password_hash=hash_password(req.password)
    )
    saved = await UserRepository.create_user(new_user)
    token = create_access_token(user_id=saved.user_id, email=saved.email)
    return AuthResponse(
        token=token,
        user_id=saved.user_id,
        email=saved.email,
        full_name=saved.full_name
    )

@router.post("/api/auth/login", response_model=AuthResponse)
async def login_user(req: LoginRequest) -> AuthResponse:
    user = await UserRepository.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user_id=user.user_id, email=user.email)
    return AuthResponse(
        token=token,
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name
    )

@router.get("/api/auth/me", response_model=UserProfile)
async def get_current_user_profile(request: Request) -> UserProfile:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
    
    token = auth_header.replace("Bearer ", "").strip()
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    user = await UserRepository.get_user_by_email(payload["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
        
    return UserProfile(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at
    )

# ==========================================
# 1. Scale & Concurrent Load APIs (v0.19.0)
# ==========================================

@router.post("/api/scale/run-load-test", response_model=LoadTestResult)
async def run_load_test(config: LoadTestConfig) -> LoadTestResult:
    return await ConcurrentLoadSimulator.run_load_test(config)

@router.get("/api/scale/load-test-results", response_model=LoadTestResult)
async def get_load_test_results() -> LoadTestResult:
    return ConcurrentLoadSimulator.get_latest_results()

# ==========================================
# 2. Observability & Prometheus Metrics (v0.15.0)
# ==========================================

@router.get("/metrics")
async def get_prometheus_metrics():
    prom_data = MetricsExporter.generate_prometheus_metrics()
    return Response(content=prom_data, media_type="text/plain")

# ==========================================
# 3. Voice AI A/B Experimentation APIs (v0.16.0)
# ==========================================

@router.get("/api/experiments/active", response_model=List[ExperimentConfig])
async def list_active_experiments() -> List[ExperimentConfig]:
    return ABExperimentManager.get_active_experiments()

@router.get("/api/experiments/{experiment_id}/results", response_model=Optional[ExperimentResult])
async def get_experiment_results(experiment_id: str) -> Optional[ExperimentResult]:
    res = ABExperimentManager.get_experiment_results(experiment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return res

# ==========================================
# 4. Evaluation Suite & Benchmark APIs (v0.17.0)
# ==========================================

@router.post("/api/evaluation/run-benchmark", response_model=BenchmarkRunSummary)
async def run_evaluation_benchmark() -> BenchmarkRunSummary:
    return BenchmarkRunner.run_evaluation_suite()

@router.get("/api/evaluation/benchmark-results", response_model=BenchmarkRunSummary)
async def get_benchmark_results() -> BenchmarkRunSummary:
    return BenchmarkRunner.get_latest_results()

# ==========================================
# 5. Multilingual & Language APIs (v0.14.0)
# ==========================================

@router.post("/api/voice/detect-language", response_model=DetectLanguageResponse)
async def detect_language(req: DetectLanguageRequest) -> DetectLanguageResponse:
    lang, conf = LanguageDetector.detect_language(req.text)
    return DetectLanguageResponse(detected_language=lang.value, confidence=conf)

# ==========================================
# 6. Agent Tools & Actions APIs (v0.13.0)
# ==========================================

@router.get("/api/agent/tools")
async def list_agent_tools() -> List[Dict[str, Any]]:
    return AgentToolExecutor.get_tool_definitions()

@router.post("/api/agent/tools/execute", response_model=ToolResult)
async def execute_agent_tool(req: ExecuteToolRequest) -> ToolResult:
    res = AgentToolExecutor.execute_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
        session_id=req.session_id
    )
    if req.session_id and req.tool_name == "generate_architecture_diagram" and res.status == "success":
        active_diagrams[req.session_id] = ArchitectureDiagramPayload(**res.output)
    return res

# ==========================================
# 7. Knowledge Base & RAG APIs (v0.11.0)
# ==========================================

@router.get("/api/knowledge/documents", response_model=List[KnowledgeDocument])
async def list_knowledge_documents() -> List[KnowledgeDocument]:
    return rag_engine.get_all_documents()

@router.post("/api/knowledge/ingest", response_model=KnowledgeDocument)
async def ingest_knowledge_document(doc: KnowledgeDocument) -> KnowledgeDocument:
    return rag_engine.ingest_document(doc)

@router.post("/api/knowledge/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge_base(req: SearchKnowledgeRequest) -> List[KnowledgeSearchResult]:
    return rag_engine.search(query=req.query, role_target=req.role_target, top_k=req.top_k)

# ==========================================
# 8. Memory & Candidate Profile APIs (v0.12.0)
# ==========================================

@router.get("/api/interview/session/{session_id}/memory", response_model=ShortTermMemory)
async def get_session_memory(session_id: str) -> ShortTermMemory:
    if session_id in active_memory_engines:
        return active_memory_engines[session_id].memory
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session.memory or ShortTermMemory()

@router.get("/api/interview/candidate/{candidate_id}/profile", response_model=CandidateProfile)
async def get_candidate_profile(candidate_id: str) -> CandidateProfile:
    return CandidateProfileRepository.get_profile(candidate_id=candidate_id)

# ==========================================
# 9. Interview Configuration & Session APIs
# ==========================================

@router.get("/api/interview/templates")
async def get_interview_templates() -> Dict[str, Any]:
    return {
        "roles": [r.value for r in InterviewRole],
        "experience_levels": [e.value for e in ExperienceLevel],
        "topics": [t.value for t in InterviewTopic],
        "languages": [l.value for l in InterviewLanguage],
        "stages": [
            {"id": s.value, "display_name": STAGE_DISPLAY_NAMES[s]}
            for s in STAGE_SEQUENCE
        ],
        "default_duration_minutes": 30
    }

@router.get("/api/interview/stages")
async def get_interview_stages(duration_minutes: int = 30) -> List[Dict[str, Any]]:
    dummy_config = InterviewConfig(duration_minutes=duration_minutes)
    sm = InterviewStateMachine(config=dummy_config)
    budgets = sm.get_budgets()
    return [b.model_dump() for b in budgets]

@router.post("/api/interview/session", response_model=InterviewSession)
async def create_interview_session(req: Request) -> InterviewSession:
    body = await req.json()
    if "config" in body:
        cfg = InterviewConfig(**body["config"])
        cand_name = body.get("candidate_name", "Candidate")
        u_email = body.get("user_email") or cfg.user_email
    else:
        cfg = InterviewConfig(**body)
        cand_name = "Candidate"
        u_email = cfg.user_email

    session = InterviewSession(
        candidate_name=cand_name,
        user_email=u_email,
        config=cfg,
        status=SessionStatus.CONFIGURED,
        current_stage=InterviewStage.GREETING
    )
    saved = await InterviewSessionRepository.create_session(session)
    active_state_machines[session.session_id] = InterviewStateMachine(config=cfg, initial_stage=InterviewStage.GREETING)
    active_adaptive_engines[session.session_id] = AdaptiveQuestionEngine(config=cfg)
    active_memory_engines[session.session_id] = InterviewMemoryEngine()
    active_languages[session.session_id] = cfg.language
    return saved

@router.get("/api/interview/session/{session_id}", response_model=InterviewSession)
async def get_interview_session(session_id: str) -> InterviewSession:
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.get("/api/interview/session/{session_id}/scorecard", response_model=SessionScorecard)
async def get_session_scorecard(session_id: str) -> SessionScorecard:
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session.scorecard or SessionScorecard()

@router.get("/api/interview/session/{session_id}/evidence-report", response_model=EvidenceEvaluationReport)
async def get_evidence_report(session_id: str) -> EvidenceEvaluationReport:
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    if session.evidence_report:
        return session.evidence_report
    
    report = EvidenceEvaluator.extract_evidence_report(session)
    await InterviewSessionRepository.update_session(session_id, {"evidence_report": report.model_dump()})
    return report

@router.post("/api/interview/session/{session_id}/generate-evidence", response_model=EvidenceEvaluationReport)
async def generate_evidence_report(session_id: str) -> EvidenceEvaluationReport:
    session = await InterviewSessionRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    report = EvidenceEvaluator.extract_evidence_report(session)
    await InterviewSessionRepository.update_session(session_id, {"evidence_report": report.model_dump()})
    return report

@router.get("/api/interview/sessions", response_model=List[InterviewSession])
async def list_interview_sessions(
    candidate_id: Optional[str] = None,
    user_email: Optional[str] = None,
    limit: int = 50
) -> List[InterviewSession]:
    return await InterviewSessionRepository.list_sessions(
        candidate_id=candidate_id,
        user_email=user_email,
        limit=limit
    )

# ==========================================
# 10. System Diagnostics & Health (v1.0.0 Production Readiness)
# ==========================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "version": settings.VERSION,
        "production_ready": True,
        "providers": {
            "stt": settings.STT_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "tts": settings.TTS_PROVIDER,
            "vad": settings.VAD_PROVIDER
        },
        "features": {
            "streaming": True,
            "barge_in": settings.BARGE_IN_ENABLED,
            "interview_foundation": True,
            "interview_state_machine": True,
            "adaptive_question_engine": True,
            "answer_evaluation": True,
            "evidence_based_evaluation": True,
            "knowledge_base_rag": True,
            "memory_and_cross_turn": True,
            "agent_tools": True,
            "multilingual_hindi_hinglish": True,
            "observability_prometheus": True,
            "ab_experimentation": True,
            "benchmark_evaluation_suite": True,
            "reliability_security": True,
            "scale_load_simulation": True,
            "production_polish": True
        }
    }

@router.get("/api/voice/status")
async def voice_status() -> Dict[str, Any]:
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
        "multilingual_support": ["English", "Hindi", "Hinglish"],
        "streaming_supported": True,
        "version": settings.VERSION
    }

# ==========================================
# 11. Voice Token & Turn Endpoints
# ==========================================

@router.post("/api/voice/token", response_model=TokenResponse)
async def get_voice_token(req: TokenRequest) -> TokenResponse:
    # Sliding window rate limiting
    if not SlidingWindowRateLimiter.is_allowed(req.identity, max_requests=100, window_seconds=60.0):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

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
    turn_span = TurnSpan(session_id=req.session_id)
    try:
        if req.audio_base64:
            audio_bytes = base64.b64decode(req.audio_base64)
        else:
            audio_bytes = b"\x00" * 3200

        history_msgs = []
        if req.history:
            for item in req.history:
                sanitized_content = PIISanitizer.sanitize(item.get("content", ""))
                history_msgs.append(LLMMessage(role=item.get("role", "user"), content=sanitized_content))

        system_prompt = None
        session = None
        current_stage = InterviewStage.GREETING
        progress_pct = 16.6
        adaptive_action = None
        turn_eval = None
        evidence_report = None
        rag_snippet = None
        memory_claims_count = 0
        contradictions: List[ContradictionItem] = []
        memory_callback = None
        active_diag = None
        active_lang = InterviewLanguage.ENGLISH
        assigned_variants = None
        
        # PII Sanitization & Phonetic Glitch Normalization
        raw_text = PIISanitizer.sanitize(req.text or "")
        phonetic_replacements = {
            "and this interview": "end this interview",
            "and the interview": "end the interview",
            "synch fuck low": "async workflow",
            "fuck low": "workflow",
            "fuck": "workflow",
            "intect": "intelligent",
            "Celerio": "Celery",
            "Larry": "Celery",
            "mango": "MongoDB",
            "dewendocker": "Docker",
            "first API": "FastAPI",
            "radius": "Redis"
        }
        cleaned_text = raw_text
        for bad, good in phonetic_replacements.items():
            cleaned_text = re.sub(re.escape(bad), good, cleaned_text, flags=re.IGNORECASE)
        candidate_text = cleaned_text.strip()

        # Check intent to end interview
        lower_cand = candidate_text.lower()
        is_end_intent = any(kw in lower_cand for kw in [
            "end this interview", "end the interview", "end interview",
            "finish interview", "stop the interview", "wrap up now", "conclude interview"
        ])
        
        # Language consistency: Strictly locked to session configuration to prevent mid-interview language flip
        active_lang = InterviewLanguage.ENGLISH

        if req.session_id:
            assigned_variants = ABExperimentManager.assign_variants(req.session_id)
            session = await InterviewSessionRepository.get_session(req.session_id)
            if session:
                active_lang = session.config.language or InterviewLanguage.ENGLISH
                active_languages[session.session_id] = active_lang
                if req.session_id not in active_state_machines:
                    active_state_machines[req.session_id] = InterviewStateMachine(
                        config=session.config,
                        initial_stage=session.current_stage
                    )
                if req.session_id not in active_adaptive_engines:
                    active_adaptive_engines[req.session_id] = AdaptiveQuestionEngine(config=session.config)
                if req.session_id not in active_memory_engines:
                    active_memory_engines[req.session_id] = InterviewMemoryEngine(initial_memory=session.memory)

                sm = active_state_machines[req.session_id]
                ae = active_adaptive_engines[req.session_id]
                me = active_memory_engines[req.session_id]
                
                if is_end_intent:
                    current_stage = InterviewStage.WRAP_UP
                    sm.current_stage = InterviewStage.WRAP_UP
                    progress_pct = 100.0
                else:
                    trans_res = sm.step_turn(last_candidate_reply=candidate_text)
                    current_stage = trans_res.current_stage
                    progress_pct = trans_res.progress_pct

                # Process working memory & claims
                new_contras = me.process_candidate_turn(
                    candidate_text=candidate_text,
                    turn_index=session.turn_count + 1,
                    stage=current_stage
                )
                contradictions = me.memory.contradictions
                memory_claims_count = len(me.memory.claims)
                memory_callback = me.generate_cross_turn_reference(current_topic=ae.get_active_topic())

                if current_stage in [InterviewStage.RESUME_DEEP_DIVE, InterviewStage.CORE_CONCEPTS, InterviewStage.SYSTEM_DESIGN]:
                    adaptive_action = ae.analyze_turn_and_plan(
                        last_candidate_reply=candidate_text,
                        current_stage=current_stage
                    )
                    turn_eval = AnswerEvaluator.evaluate_turn(
                        candidate_reply=candidate_text,
                        topic=ae.get_active_topic(),
                        stage=current_stage
                    )

                # Mid-interview RAG query
                search_q = candidate_text or ae.get_active_topic()
                rag_results = rag_engine.search(query=search_q, role_target=session.config.role.value, top_k=1)
                if rag_results:
                    rag_snippet = f"{rag_results[0].title}: {rag_results[0].matched_snippet}"

                # System Design automatic diagram synthesis tool invocation
                if current_stage == InterviewStage.SYSTEM_DESIGN or "architecture" in candidate_text.lower():
                    components = ["Client", "API Gateway", "Backend Service", "PostgreSQL", "Redis"]
                    diag_payload = AgentToolExecutor.generate_architecture_diagram(
                        components=components,
                        title=f"{session.candidate_name}'s Architecture Design"
                    )
                    active_diagrams[session.session_id] = diag_payload
                    active_diag = diag_payload
                elif session.session_id in active_diagrams:
                    active_diag = active_diagrams[session.session_id]
                
                system_prompt = InterviewPromptBuilder.build_system_prompt(
                    config=session.config,
                    candidate_name=session.candidate_name,
                    stage=current_stage,
                    adaptive_action=adaptive_action,
                    rag_context=rag_snippet,
                    memory_context=memory_callback,
                    current_language=active_lang
                )

        if req.text and isinstance(voice_pipeline.stt, type(VoiceProviderFactory.get_stt_provider("mock"))):
            voice_pipeline.stt.default_response = candidate_text

        turn_result: PipelineTurnResult = await voice_pipeline.process_turn(
            audio_in=audio_bytes,
            input_text=candidate_text,
            history=history_msgs,
            system_prompt=system_prompt,
            language="hi" if active_lang in [InterviewLanguage.HINDI, InterviewLanguage.HINGLISH] else "en"
        )

        turn_span.stt_latency_ms = getattr(turn_result.metrics, "stt_latency_ms", 0.0)
        turn_span.llm_ttft_ms = getattr(turn_result.metrics, "llm_ttft_ms", getattr(turn_result.metrics, "llm_latency_ms", 150.0))
        turn_span.llm_total_ms = getattr(turn_result.metrics, "llm_total_ms", getattr(turn_result.metrics, "llm_latency_ms", 300.0))
        turn_span.tts_ttfa_ms = getattr(turn_result.metrics, "tts_ttfa_ms", getattr(turn_result.metrics, "tts_latency_ms", 120.0))
        turn_span.tts_total_ms = getattr(turn_result.metrics, "tts_total_ms", getattr(turn_result.metrics, "tts_latency_ms", 250.0))
        turn_span.language = active_lang.value
        MetricsExporter.record_span(turn_span)

        if session:
            sanitized_transcript = PIISanitizer.sanitize(turn_result.transcript)
            session.transcripts.append(TranscriptEntry(
                stage=current_stage,
                role="candidate", 
                text=sanitized_transcript,
                evaluated_depth=adaptive_action.evaluated_depth.value if adaptive_action else None,
                adaptive_strategy=adaptive_action.strategy.value if adaptive_action else None,
                evaluation=turn_eval
            ))
            session.transcripts.append(TranscriptEntry(
                stage=current_stage,
                role="interviewer", 
                text=turn_result.response_text, 
                metrics=turn_result.metrics.model_dump()
            ))
            session.turn_count += 1
            session.current_stage = current_stage
            session.stage_turn_counts = sm.stage_turn_counts
            session.topic_coverage = ae.topic_stats if 'ae' in locals() else {}
            session.memory = me.memory if 'me' in locals() else ShortTermMemory()

            all_evals = [t.evaluation for t in session.transcripts if t.evaluation is not None]
            session.scorecard = AnswerEvaluator.aggregate_scorecard(all_evals)
            session.evidence_report = EvidenceEvaluator.extract_evidence_report(session)
            evidence_report = session.evidence_report

            # Record long-term candidate profile
            CandidateProfileRepository.record_session_completion(session)

            # Record A/B experiment metrics
            if assigned_variants:
                for exp_id, var_id in assigned_variants.items():
                    ABExperimentManager.record_metric(
                        experiment_id=exp_id,
                        variant_id=var_id,
                        turn_latency_ms=getattr(turn_result.metrics, "total_turn_ms", getattr(turn_result.metrics, "total_latency_ms", 300.0)),
                        ttft_ms=getattr(turn_result.metrics, "llm_ttft_ms", getattr(turn_result.metrics, "llm_latency_ms", 150.0)),
                        scorecard_score=session.scorecard.overall_score if session.scorecard else 3.0
                    )

            await InterviewSessionRepository.update_session(session.session_id, {
                "transcripts": [t.model_dump() for t in session.transcripts],
                "turn_count": session.turn_count,
                "current_stage": session.current_stage.value,
                "stage_turn_counts": session.stage_turn_counts,
                "topic_coverage": session.topic_coverage,
                "scorecard": session.scorecard.model_dump(),
                "evidence_report": session.evidence_report.model_dump(),
                "memory": session.memory.model_dump()
            })

        return VoiceTurnResponse(
            transcript=turn_result.transcript,
            response_text=turn_result.response_text,
            audio_base64=base64.b64encode(turn_result.audio_bytes).decode("utf-8"),
            audio_format=turn_result.audio_format,
            current_stage=current_stage.value,
            stage_display_name=STAGE_DISPLAY_NAMES[current_stage],
            progress_pct=progress_pct,
            detected_language=active_lang.value,
            adaptive_strategy=adaptive_action.strategy_display if adaptive_action else None,
            evaluated_depth=adaptive_action.evaluated_depth.value if adaptive_action else None,
            turn_evaluation=turn_eval,
            scorecard=session.scorecard if session else None,
            evidence_report=evidence_report,
            rag_snippet=rag_snippet,
            memory_claims_count=memory_claims_count,
            contradictions=contradictions,
            active_diagram=active_diag,
            assigned_variants=assigned_variants,
            topic_coverage=session.topic_coverage if session else None,
            metrics=turn_result.metrics.model_dump()
        )
    except Exception as e:
        logger.error(f"Turn processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Turn processing failed: {str(e)}"
        )

@router.websocket("/api/voice/stream/ws")
async def voice_streaming_websocket(websocket: WebSocket):
    """
    Full-duplex WebSocket endpoint for real-time streaming voice sessions with Answer, Evidence Evaluation, Knowledge RAG, Memory, Tool Calling, Multilingual Code-Switching, PII Redaction, and Observability Spans.
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
            
            system_prompt = None
            current_stage = InterviewStage.GREETING
            adaptive_action = None
            turn_eval = None
            rag_snippet = None
            memory_callback = None
            active_lang = InterviewLanguage.ENGLISH

            candidate_text = PIISanitizer.sanitize(text or "")
            if candidate_text:
                detected_lang, _ = LanguageDetector.detect_language(candidate_text)
                active_lang = detected_lang
            
            if session_id:
                session = await InterviewSessionRepository.get_session(session_id)
                if session:
                    if session_id not in active_state_machines:
                        active_state_machines[session_id] = InterviewStateMachine(
                            config=session.config,
                            initial_stage=session.current_stage
                        )
                    if session_id not in active_adaptive_engines:
                        active_adaptive_engines[session_id] = AdaptiveQuestionEngine(config=session.config)
                    if session_id not in active_memory_engines:
                        active_memory_engines[session_id] = InterviewMemoryEngine(initial_memory=session.memory)

                    sm = active_state_machines[session_id]
                    ae = active_adaptive_engines[session_id]
                    me = active_memory_engines[session_id]
                    
                    # Language tracking
                    prev_lang = active_languages.get(session_id, session.config.language)
                    if active_lang != prev_lang and candidate_text:
                        await websocket.send_json({
                            "event_type": "language_switched",
                            "previous_language": prev_lang.value,
                            "current_language": active_lang.value
                        })
                    active_languages[session_id] = active_lang
                    
                    trans_res = sm.step_turn(last_candidate_reply=candidate_text)
                    current_stage = trans_res.current_stage

                    # Process memory
                    new_contras = me.process_candidate_turn(
                        candidate_text=candidate_text,
                        turn_index=session.turn_count + 1,
                        stage=current_stage
                    )
                    memory_callback = me.generate_cross_turn_reference(current_topic=ae.get_active_topic())

                    if current_stage in [InterviewStage.RESUME_DEEP_DIVE, InterviewStage.CORE_CONCEPTS, InterviewStage.SYSTEM_DESIGN]:
                        adaptive_action = ae.analyze_turn_and_plan(
                            last_candidate_reply=candidate_text,
                            current_stage=current_stage
                        )
                        turn_eval = AnswerEvaluator.evaluate_turn(
                            candidate_reply=candidate_text,
                            topic=ae.get_active_topic(),
                            stage=current_stage
                        )

                    # RAG lookup
                    search_q = candidate_text or ae.get_active_topic()
                    rag_results = rag_engine.search(query=search_q, role_target=session.config.role.value, top_k=1)
                    if rag_results:
                        rag_snippet = f"{rag_results[0].title}: {rag_results[0].matched_snippet}"

                    # Tool call check: Diagram generation
                    if current_stage == InterviewStage.SYSTEM_DESIGN:
                        components = ["Client", "API Gateway", "Backend Service", "PostgreSQL", "Redis"]
                        diag_payload = AgentToolExecutor.generate_architecture_diagram(
                            components=components,
                            title=f"{session.candidate_name}'s Architecture Design"
                        )
                        active_diagrams[session.session_id] = diag_payload
                        await websocket.send_json({
                            "event_type": "tool_executed",
                            "tool_name": "generate_architecture_diagram",
                            "output": diag_payload.model_dump()
                        })

                    # Emit stage transition event if advanced
                    if trans_res.transitioned:
                        await websocket.send_json({
                            "event_type": "stage_transition",
                            "stage": current_stage.value,
                            "stage_display_name": trans_res.stage_display_name,
                            "progress_pct": trans_res.progress_pct
                        })

                    # Emit adaptive action and turn evaluation
                    if adaptive_action:
                        await websocket.send_json({
                            "event_type": "adaptive_action",
                            "strategy_display": adaptive_action.strategy_display,
                            "evaluated_depth": adaptive_action.evaluated_depth.value,
                            "topic": adaptive_action.target_topic
                        })

                    if new_contras:
                        await websocket.send_json({
                            "event_type": "contradiction_detected",
                            "contradiction": new_contras[0].model_dump()
                        })

                    if turn_eval:
                        await websocket.send_json({
                            "event_type": "turn_evaluation",
                            "evaluation": turn_eval.model_dump(),
                            "rag_snippet": rag_snippet,
                            "memory_claims_count": len(me.memory.claims),
                            "detected_language": active_lang.value
                        })

                    system_prompt = InterviewPromptBuilder.build_system_prompt(
                        config=session.config,
                        candidate_name=session.candidate_name,
                        stage=current_stage,
                        adaptive_action=adaptive_action,
                        rag_context=rag_snippet,
                        memory_context=memory_callback,
                        current_language=active_lang
                    )

            history_msgs = [
                LLMMessage(role=m.get("role", "user"), content=PIISanitizer.sanitize(m.get("content", "")))
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
                    "stage": current_stage.value,
                    "adaptive_strategy": adaptive_action.strategy_display if adaptive_action else None,
                    "rag_snippet": rag_snippet,
                    "detected_language": active_lang.value,
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
