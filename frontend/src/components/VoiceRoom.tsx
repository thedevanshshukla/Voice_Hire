import React, { useState, useEffect, useRef } from 'react';
import type { InterviewSession } from './InterviewSetup';

interface VoiceMetrics {
  stt_latency_ms?: number;
  llm_ttft_ms?: number;
  llm_total_ms?: number;
  tts_ttfa_ms?: number;
  tts_total_ms?: number;
  speech_duration_ms?: number;
  pause_count?: number;
  endpointing_delay_ms?: number;
  interrupted?: boolean;
  interruption_count?: number;
  interruption_detection_ms?: number;
  cancellation_latency_ms?: number;
  interrupted_at_word?: string;
  total_perceived_ms?: number;
  total_turn_ms?: number;
  total_latency_ms?: number;
}

interface TurnEvaluation {
  overall_score: number;
  correctness: number;
  depth_and_mechanics: number;
  communication_clarity: number;
  tradeoff_awareness: number;
  practical_vs_theory: number;
  strengths: string[];
  gaps: string[];
  feedback: string;
}

interface SessionScorecard {
  overall_score: number;
  avg_correctness: number;
  avg_depth: number;
  avg_clarity: number;
  avg_tradeoffs: number;
  avg_practical: number;
  total_evaluated_turns: number;
  passed_recommendation: boolean;
  summary_verdict: string;
  top_strengths: string[];
  areas_for_improvement: string[];
}

interface EvidenceSnippet {
  quote: string;
  topic: string;
  stage: string;
  dimension: string;
  rationale: string;
}

interface RedFlagItem {
  category: string;
  quote: string;
  severity: string;
  explanation: string;
}

interface EvidenceEvaluationReport {
  session_id: string;
  candidate_name: string;
  confidence_score: number;
  recommendation: string;
  recommendation_reasoning: string;
  key_strengths_with_evidence: EvidenceSnippet[];
  key_weaknesses_with_evidence: EvidenceSnippet[];
  red_flags: RedFlagItem[];
  generated_at: string;
}

interface TranscriptMessage {
  id: string;
  role: 'candidate' | 'interviewer';
  text: string;
  stage?: string;
  adaptiveStrategy?: string;
  evaluation?: TurnEvaluation;
  audioBase64?: string;
  metrics?: VoiceMetrics;
  isStreaming?: boolean;
  wasInterrupted?: boolean;
  timestamp: string;
}

interface VoiceRoomProps {
  apiUrl: string;
  activeSession?: InterviewSession | null;
  onClose?: () => void;
}

const STAGES = [
  { id: 'greeting', label: '1. Intro', icon: '👋' },
  { id: 'resume_deep_dive', label: '2. Past Projects', icon: '📂' },
  { id: 'core_concepts', label: '3. Core Concepts', icon: '🧠' },
  { id: 'system_design', label: '4. System Design', icon: '🏛️' },
  { id: 'candidate_questions', label: '5. Q&A', icon: '❓' },
  { id: 'wrap_up', label: '6. Wrap-Up', icon: '🏁' }
];

export const VoiceRoom: React.FC<VoiceRoomProps> = ({ apiUrl, activeSession, onClose }) => {
  const [roomName, setRoomName] = useState(activeSession ? activeSession.session_id : 'interview-session-01');
  const [candidateName, setCandidateName] = useState(activeSession ? activeSession.candidate_name : 'Candidate');
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useStreamingMode, setUseStreamingMode] = useState(true);
  const [silenceThresholdMs, setSilenceThresholdMs] = useState(800);
  const [vadState, setVadState] = useState<'idle' | 'speaking' | 'paused' | 'endpoint'>('idle');
  const [currentStage, setCurrentStage] = useState<string>('greeting');
  const [stageProgressPct, setStageProgressPct] = useState<number>(16.6);
  const [stageNotification, setStageNotification] = useState<string | null>(null);
  const [adaptiveStrategy, setAdaptiveStrategy] = useState<string | null>(null);
  const [activeRagSnippet, setActiveRagSnippet] = useState<string | null>(null);
  const [memoryClaimsCount, setMemoryClaimsCount] = useState<number>(0);
  const [lastContradiction, setLastContradiction] = useState<string | null>(null);
  
  const [sessionScorecard, setSessionScorecard] = useState<SessionScorecard | null>(null);
  const [evidenceReport, setEvidenceReport] = useState<EvidenceEvaluationReport | null>(null);
  const [modalTab, setModalTab] = useState<'scorecard' | 'evidence' | 'tools' | 'benchmark'>('scorecard');
  const [activeDiagram, setActiveDiagram] = useState<any>(null);
  const [sandboxCode, setSandboxCode] = useState<string>('def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n\nprint("Result:", two_sum([2, 7, 11, 15], 9))');
  const [sandboxOutput, setSandboxOutput] = useState<any>(null);
  const [isExecutingCode, setIsExecutingCode] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [assignedVariants, setAssignedVariants] = useState<Record<string, string> | null>(null);
  const [latestTurnScore, setLatestTurnScore] = useState<number | null>(null);
  const [detectedLanguage, setDetectedLanguage] = useState<string>(activeSession?.config.language || 'English');
  const [showScorecardModal, setShowScorecardModal] = useState<boolean>(false);

  const [inputText, setInputText] = useState('');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string>('');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [agentStatus, setAgentStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeMetrics, setActiveMetrics] = useState<VoiceMetrics | null>(null);
  const [lastInterruption, setLastInterruption] = useState<string | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);

  // Auto-connect if activeSession is passed
  useEffect(() => {
    if (activeSession && !isConnected) {
      handleConnect();
    }
  }, [activeSession]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  // Fetch updated session scorecard & evidence report
  const refreshScorecardAndEvidence = async () => {
    if (!activeSession) return;
    try {
      const [scRes, evRes] = await Promise.all([
        fetch(`${apiUrl}/api/interview/session/${activeSession.session_id}/scorecard`),
        fetch(`${apiUrl}/api/interview/session/${activeSession.session_id}/evidence-report`)
      ]);
      if (scRes.ok) {
        const sc = await scRes.json();
        setSessionScorecard(sc);
      }
      if (evRes.ok) {
        const ev = await evRes.json();
        setEvidenceReport(ev);
      }
    } catch (err) {
      console.warn('Could not refresh scorecard/evidence:', err);
    }
  };

  // Immediately stop active audio playback (Barge-In)
  const cancelActiveAudio = () => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }
  };

  // Trigger Barge-In / Interruption
  const handleInterrupt = () => {
    cancelActiveAudio();
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'interrupt', reason: 'manual_barge_in' }));
    }
    setAgentStatus('listening');
    setLastInterruption(`🛑 Agent interrupted by candidate`);
    setTimeout(() => setLastInterruption(null), 3000);
  };

  // Connect to LiveKit session via Token API & setup WebSocket for streaming
  const handleConnect = async () => {
    setErrorMsg(null);
    try {
      const res = await fetch(`${apiUrl}/api/voice/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: activeSession ? activeSession.session_id : roomName,
          identity: `candidate-${Date.now()}`,
          name: candidateName,
          session_id: activeSession?.session_id
        })
      });

      if (!res.ok) {
        throw new Error(`Token endpoint returned ${res.status}`);
      }

      const data = await res.json();
      setSessionToken(data.token);
      setLivekitUrl(data.url);
      setIsConnected(true);
      setAgentStatus('listening');
      setVadState('idle');

      // Initial greeting message tailored to role
      const roleName = activeSession?.config?.role || 'Software Engineer';
      const initialGreeting: TranscriptMessage = {
        id: 'msg-0',
        role: 'interviewer',
        stage: 'greeting',
        text: `Hello ${candidateName}! Welcome to your technical interview for the ${roleName} position. Could you introduce yourself and tell me about a complex project you recently architected?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      setMessages([initialGreeting]);
    } catch (err: any) {
      console.error('Connection error:', err);
      setErrorMsg(err.message || 'Failed to connect to voice session');
    }
  };

  const handleDisconnect = () => {
    cancelActiveAudio();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setSessionToken(null);
    setAgentStatus('idle');
    setVadState('idle');
    setActiveMetrics(null);
    if (onClose) onClose();
  };

  // Play audio from base64 string
  const playAudio = (base64Audio: string) => {
    try {
      cancelActiveAudio();
      const snd = new Audio(`data:audio/wav;base64,${base64Audio}`);
      activeAudioRef.current = snd;
      snd.play().catch((e) => console.warn('Audio play prevented:', e));
    } catch (err) {
      console.error('Error playing audio:', err);
    }
  };

  const handleRunSandboxCode = async () => {
    setIsExecutingCode(true);
    try {
      const res = await fetch(`${apiUrl}/api/agent/tools/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: 'execute_code_snippet',
          arguments: { code: sandboxCode },
          session_id: activeSession?.session_id
        })
      });
      if (res.ok) {
        const data = await res.json();
        setSandboxOutput(data.output);
      }
    } catch (err) {
      console.error('Failed to run sandbox code:', err);
    } finally {
      setIsExecutingCode(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    try {
      const res = await fetch(`${apiUrl}/api/evaluation/run-benchmark`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setBenchmarkData(data);
      }
    } catch (err) {
      console.error('Benchmark error:', err);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  // Process streaming turn over WebSocket with Answer & Evidence Evaluation
  const handleSendStreamingTurn = async (textToSend: string, userMsgId: string) => {
    cancelActiveAudio();
    const wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/voice/stream/ws';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    const agentMsgId = `agent-${Date.now()}`;
    let fullAgentText = '';

    ws.onopen = () => {
      setAgentStatus('thinking');
      setVadState('endpoint');
      const historyPayload = messages.map((m) => ({
        role: m.role === 'candidate' ? 'user' : 'assistant',
        content: m.text
      }));

      setMessages((prev) => [
        ...prev,
        {
          id: agentMsgId,
          role: 'interviewer',
          stage: currentStage,
          text: '...',
          isStreaming: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        }
      ]);

      ws.send(JSON.stringify({
        action: 'turn',
        text: textToSend,
        session_id: activeSession?.session_id,
        history: historyPayload
      }));
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.event_type === 'stage_transition') {
          setCurrentStage(payload.stage);
          setStageProgressPct(payload.progress_pct);
          setStageNotification(`🎯 Stage Advanced: ${payload.stage_display_name}`);
          setTimeout(() => setStageNotification(null), 4000);
        } else if (payload.event_type === 'adaptive_action') {
          setAdaptiveStrategy(payload.strategy_display);
        } else if (payload.event_type === 'turn_evaluation') {
          const ev: TurnEvaluation = payload.evaluation;
          setLatestTurnScore(ev.overall_score);
          if (payload.rag_snippet) {
            setActiveRagSnippet(payload.rag_snippet);
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === userMsgId ? { ...msg, evaluation: ev } : msg
            )
          );
          refreshScorecardAndEvidence();
        } else if (payload.event_type === 'contradiction_detected') {
          setLastContradiction(`⚠️ Contradiction: ${payload.contradiction.explanation}`);
          setTimeout(() => setLastContradiction(null), 5000);
        } else if (payload.event_type === 'language_switched') {
          setDetectedLanguage(payload.current_language);
          setStageNotification(`🌐 Language Switched: ${payload.current_language}`);
          setTimeout(() => setStageNotification(null), 4000);
        } else if (payload.event_type === 'tool_executed' && payload.tool_name === 'generate_architecture_diagram') {
          setActiveDiagram(payload.output);
        } else if (payload.rag_snippet) {
          setActiveRagSnippet(payload.rag_snippet);
        }
        if (payload.detected_language) {
          setDetectedLanguage(payload.detected_language);
        }
        if (payload.assigned_variants) {
          setAssignedVariants(payload.assigned_variants);
        }
        if (payload.memory_claims_count !== undefined) {
          setMemoryClaimsCount(payload.memory_claims_count);
        } else if (payload.event_type === 'vad_event') {
          if (payload.vad_status === 'candidate_speaking') setVadState('speaking');
          else if (payload.vad_status === 'candidate_paused') setVadState('paused');
          else if (payload.vad_status === 'turn_endpoint') setVadState('endpoint');
        } else if (payload.event_type === 'token') {
          fullAgentText += payload.text;
          setAgentStatus('speaking');
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMsgId ? { ...msg, text: fullAgentText } : msg
            )
          );
        } else if (payload.event_type === 'audio_chunk' && payload.audio_chunk_b64) {
          playAudio(payload.audio_chunk_b64);
        } else if (payload.event_type === 'interrupted') {
          cancelActiveAudio();
          setAgentStatus('listening');
          setLastInterruption('🛑 Agent Barge-in Cutoff (<150ms)');
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMsgId
                ? { ...msg, text: fullAgentText + ' [interrupted]', isStreaming: false, wasInterrupted: true }
                : msg
            )
          );
          setTimeout(() => setLastInterruption(null), 3000);
        } else if (payload.event_type === 'metrics') {
          setActiveMetrics(payload.metrics);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMsgId
                ? { ...msg, text: payload.text || fullAgentText, metrics: payload.metrics, isStreaming: false }
                : msg
            )
          );
        } else if (payload.event_type === 'done') {
          ws.close();
          setIsProcessing(false);
          setVadState('idle');
          setTimeout(() => setAgentStatus('listening'), 1500);
        }
      } catch (err) {
        console.error('WS message parse error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setErrorMsg('Streaming connection error');
      setIsProcessing(false);
      setAgentStatus('listening');
      setVadState('idle');
    };
  };

  // Submit voice / text turn to backend
  const handleSendTurn = async (customText?: string) => {
    cancelActiveAudio();
    const textToSend = customText || inputText;
    if (!textToSend.trim() || isProcessing) return;

    setErrorMsg(null);
    setIsProcessing(true);
    setVadState('speaking');

    const userMsgId = `user-${Date.now()}`;
    const userMsg: TranscriptMessage = {
      id: userMsgId,
      role: 'candidate',
      stage: currentStage,
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    if (useStreamingMode) {
      handleSendStreamingTurn(textToSend, userMsgId);
      return;
    }

    // Standard REST Fallback
    setAgentStatus('thinking');
    try {
      const historyPayload = messages.map((m) => ({
        role: m.role === 'candidate' ? 'user' : 'assistant',
        content: m.text
      }));

      const res = await fetch(`${apiUrl}/api/voice/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession?.session_id,
          text: textToSend,
          language: 'en',
          history: historyPayload
        })
      });

      if (!res.ok) {
        throw new Error(`Turn endpoint returned ${res.status}`);
      }

      const data = await res.json();
      setAgentStatus('speaking');
      setActiveMetrics(data.metrics);
      if (data.current_stage) {
        setCurrentStage(data.current_stage);
        setStageProgressPct(data.progress_pct);
      }
      if (data.adaptive_strategy) {
        setAdaptiveStrategy(data.adaptive_strategy);
      }
      if (data.turn_evaluation) {
        setLatestTurnScore(data.turn_evaluation.overall_score);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === userMsgId ? { ...msg, evaluation: data.turn_evaluation } : msg
          )
        );
      }
      if (data.scorecard) {
        setSessionScorecard(data.scorecard);
      }
      if (data.evidence_report) {
        setEvidenceReport(data.evidence_report);
      }
      if (data.assigned_variants) {
        setAssignedVariants(data.assigned_variants);
      }

      const agentMsg: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
        stage: data.current_stage || currentStage,
        adaptiveStrategy: data.adaptive_strategy,
        text: data.response_text,
        audioBase64: data.audio_base64,
        metrics: data.metrics,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };

      setMessages((prev) => [...prev, agentMsg]);

      if (data.audio_base64) {
        playAudio(data.audio_base64);
      }

      setTimeout(() => {
        setAgentStatus('listening');
        setVadState('idle');
      }, 2000);
    } catch (err: any) {
      console.error('Turn error:', err);
      setErrorMsg(err.message || 'Error processing speech turn');
      setAgentStatus('listening');
      setVadState('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  const getStageIndex = (stageId: string) => STAGES.findIndex((s) => s.id === stageId);

  return (
    <div className="voice-room-container">
      {/* Header bar */}
      <div className="voice-room-header">
        <div className="room-info">
          <div className={`status-indicator ${isConnected ? 'active' : 'inactive'}`} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 className="room-title">
                {activeSession ? `${activeSession.config.role} Interview` : `Room: ${roomName}`}
              </h3>
              {activeSession && (
                <span className="badge badge-sm">{activeSession.config.experience_level}</span>
              )}
            </div>
            <span className="room-subtitle">
              {isConnected ? `Candidate: ${candidateName} • ${agentStatus.toUpperCase()}` : 'LiveKit WebRTC Evidence-Based Evaluation v0.10.0'}
            </span>
          </div>
        </div>

        {/* Topics pill tags */}
        {activeSession?.config?.topics && (
          <div className="header-topics-bar">
            {activeSession.config.topics.map((t, idx) => (
              <span key={idx} className="header-topic-chip">{t}</span>
            ))}
          </div>
        )}

        <div className="room-actions">
          {isConnected && (
            <button 
              className="btn btn-secondary btn-scorecard-btn"
              onClick={() => {
                refreshScorecardAndEvidence();
                setShowScorecardModal(true);
              }}
            >
              <span>📊 Scorecard & Evidence</span>
              {sessionScorecard && (
                <span className="scorecard-tag">{sessionScorecard.overall_score.toFixed(1)}</span>
              )}
            </button>
          )}
          {isConnected && (
            <div className="mode-toggle">
              <label className="switch-label">
                <input
                  type="checkbox"
                  checked={useStreamingMode}
                  onChange={(e) => setUseStreamingMode(e.target.checked)}
                />
                <span>⚡ Stream</span>
              </label>
            </div>
          )}
          {isConnected ? (
            <button className="btn btn-disconnect" onClick={handleDisconnect}>
              End Interview
            </button>
          ) : null}
          {onClose && (
            <button className="btn btn-secondary btn-icon" onClick={onClose}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* 6-Stage Progression Timeline */}
      {isConnected && (
        <div className="stage-timeline-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '900px', margin: '0 auto 8px auto' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
              Interview Progression
            </span>
            <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: 700, color: 'var(--accent-purple)' }}>
              {stageProgressPct}% Complete
            </span>
          </div>
          <div className="stage-timeline">
            {STAGES.map((s, idx) => {
              const currentIndex = getStageIndex(currentStage);
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;
              return (
                <div 
                  key={s.id} 
                  className={`timeline-step ${isPast ? 'completed' : ''} ${isCurrent ? 'active' : ''}`}
                >
                  <div className="step-bullet">
                    {isPast ? '✓' : s.icon}
                  </div>
                  <span className="step-label">{s.label}</span>
                  {idx < STAGES.length - 1 && <div className="step-connector"></div>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="error-banner">
          ⚠️ {errorMsg}
        </div>
      )}

      {stageNotification && (
        <div className="stage-notification-banner">
          {stageNotification}
        </div>
      )}

      {lastInterruption && (
        <div className="interruption-banner">
          {lastInterruption}
        </div>
      )}

      {lastContradiction && (
        <div className="contradiction-banner">
          {lastContradiction}
        </div>
      )}

      {/* Live Scorecard & Evidence Report Modal */}
      {showScorecardModal && (
        <div className="scorecard-modal-backdrop" onClick={() => setShowScorecardModal(false)}>
          <div className="scorecard-modal" onClick={(e) => e.stopPropagation()}>
            <div className="scorecard-modal-header">
              <div>
                <h3>Evaluation & Evidence Audit</h3>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {activeSession?.config.role} • {candidateName}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <div className="modal-tabs">
                  <button 
                    className={`tab-btn ${modalTab === 'scorecard' ? 'active' : ''}`}
                    onClick={() => setModalTab('scorecard')}
                  >
                    Scorecard
                  </button>
                  <button 
                    className={`tab-btn ${modalTab === 'evidence' ? 'active' : ''}`}
                    onClick={() => setModalTab('evidence')}
                  >
                    Evidence & Red Flags ({evidenceReport?.red_flags?.length || 0})
                  </button>
                  <button 
                    className={`tab-btn ${modalTab === 'tools' ? 'active' : ''}`}
                    onClick={() => setModalTab('tools')}
                  >
                    🛠️ Architecture & Tools
                  </button>
                  <button 
                    className={`tab-btn ${modalTab === 'benchmark' ? 'active' : ''}`}
                    onClick={() => {
                      setModalTab('benchmark');
                      if (!benchmarkData) handleRunBenchmark();
                    }}
                  >
                    🧪 Benchmarks
                  </button>
                </div>
                <button className="btn-close" onClick={() => setShowScorecardModal(false)}>✕</button>
              </div>
            </div>

            <div className="scorecard-modal-body">
              {modalTab === 'scorecard' ? (
                <>
                  <div className="scorecard-hero">
                    <div className="hero-score-val">
                      {sessionScorecard?.overall_score.toFixed(1) || '0.0'}
                      <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 5.0</span>
                    </div>
                    <div className="hero-verdict">
                      <div className="verdict-label">Verdict</div>
                      <div className="verdict-title">{sessionScorecard?.summary_verdict || 'In Progress'}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {sessionScorecard?.total_evaluated_turns || 0} technical answers evaluated
                      </div>
                    </div>
                  </div>

                  {/* 5-Dimensional Radar Progress Bars */}
                  <div className="dimensions-breakdown">
                    <h4>Dimensional Breakdown</h4>
                    
                    <div className="dim-row">
                      <div className="dim-header">
                        <span>1. Technical Correctness</span>
                        <span className="dim-val">{sessionScorecard?.avg_correctness.toFixed(1) || '0.0'} / 5.0</span>
                      </div>
                      <div className="dim-bar-bg">
                        <div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_correctness || 0) / 5) * 100}%` }}></div>
                      </div>
                    </div>

                    <div className="dim-row">
                      <div className="dim-header">
                        <span>2. Depth & Mechanics</span>
                        <span className="dim-val">{sessionScorecard?.avg_depth.toFixed(1) || '0.0'} / 5.0</span>
                      </div>
                      <div className="dim-bar-bg">
                        <div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_depth || 0) / 5) * 100}%`, background: 'var(--accent-purple)' }}></div>
                      </div>
                    </div>

                    <div className="dim-row">
                      <div className="dim-header">
                        <span>3. Trade-off Awareness</span>
                        <span className="dim-val">{sessionScorecard?.avg_tradeoffs.toFixed(1) || '0.0'} / 5.0</span>
                      </div>
                      <div className="dim-bar-bg">
                        <div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_tradeoffs || 0) / 5) * 100}%`, background: 'var(--accent-green)' }}></div>
                      </div>
                    </div>

                    <div className="dim-row">
                      <div className="dim-header">
                        <span>4. Practical vs Theory</span>
                        <span className="dim-val">{sessionScorecard?.avg_practical.toFixed(1) || '0.0'} / 5.0</span>
                      </div>
                      <div className="dim-bar-bg">
                        <div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_practical || 0) / 5) * 100}%`, background: 'var(--accent-yellow)' }}></div>
                      </div>
                    </div>

                    <div className="dim-row">
                      <div className="dim-header">
                        <span>5. Communication Clarity</span>
                        <span className="dim-val">{sessionScorecard?.avg_clarity.toFixed(1) || '0.0'} / 5.0</span>
                      </div>
                      <div className="dim-bar-bg">
                        <div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_clarity || 0) / 5) * 100}%`, background: 'var(--accent-blue)' }}></div>
                      </div>
                    </div>
                  </div>

                  {/* Strengths & Gaps */}
                  <div className="scorecard-notes-grid">
                    <div className="notes-box strengths">
                      <h5>🌟 Top Strengths</h5>
                      <ul>
                        {sessionScorecard?.top_strengths?.map((s, idx) => (
                          <li key={idx}>{s}</li>
                        )) || <li>Evaluating answers...</li>}
                      </ul>
                    </div>
                    <div className="notes-box gaps">
                      <h5>⚠️ Areas for Growth</h5>
                      <ul>
                        {sessionScorecard?.areas_for_improvement?.map((g, idx) => (
                          <li key={idx}>{g}</li>
                        )) || <li>Evaluating answers...</li>}
                      </ul>
                    </div>
                  </div>
                </>
              ) : modalTab === 'evidence' ? (
                /* Evidence & Red Flags Tab */
                <div className="evidence-tab-content">
                  {/* Executive Summary Card */}
                  <div className="evidence-executive-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span className={`recommendation-badge ${evidenceReport?.recommendation?.toLowerCase()}`}>
                        {evidenceReport?.recommendation || 'EVALUATING'}
                      </span>
                      <span className="confidence-tag">
                        🎯 {Math.round((evidenceReport?.confidence_score || 0.8) * 100)}% Confidence
                      </span>
                    </div>
                    <p className="recommendation-reasoning">
                      {evidenceReport?.recommendation_reasoning || 'Conducting turn evaluations to gather transcript evidence.'}
                    </p>
                  </div>

                  {/* Red Flags Section */}
                  {evidenceReport?.red_flags && evidenceReport.red_flags.length > 0 && (
                    <div className="red-flags-section">
                      <h4 style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        🚩 Detected Technical Red Flags ({evidenceReport.red_flags.length})
                      </h4>
                      <div className="red-flags-grid">
                        {evidenceReport.red_flags.map((rf, idx) => (
                          <div key={idx} className="red-flag-card">
                            <div className="red-flag-top">
                              <span className={`severity-badge ${rf.severity.toLowerCase()}`}>{rf.severity}</span>
                              <span className="flag-category">{rf.category}</span>
                            </div>
                            <div className="flag-quote">"{rf.quote}"</div>
                            <div className="flag-explanation">⚠️ {rf.explanation}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Transcript Quotation Citations */}
                  <div className="evidence-quotes-section">
                    <h4>💬 Verbatim Transcript Citations</h4>
                    
                    <div className="evidence-quotes-grid">
                      {evidenceReport?.key_strengths_with_evidence?.map((snip, idx) => (
                        <div key={idx} className="quote-evidence-card strength">
                          <div className="quote-header">
                            <span className="quote-tag strength">STRENGTH • {snip.dimension}</span>
                            <span className="quote-stage">{snip.stage}</span>
                          </div>
                          <div className="quote-body">"{snip.quote}"</div>
                          <div className="quote-rationale">✓ {snip.rationale}</div>
                        </div>
                      ))}

                      {evidenceReport?.key_weaknesses_with_evidence?.map((snip, idx) => (
                        <div key={idx} className="quote-evidence-card gap">
                          <div className="quote-header">
                            <span className="quote-tag gap">GAP • {snip.dimension}</span>
                            <span className="quote-stage">{snip.stage}</span>
                          </div>
                          <div className="quote-body">"{snip.quote}"</div>
                          <div className="quote-rationale">⚠️ {snip.rationale}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : modalTab === 'tools' ? (
                /* Tools & Architecture Tab */
                <div className="tools-tab-content">
                  {/* System Architecture Diagram Card */}
                  <div className="tool-card">
                    <div className="tool-card-header">
                      <h4>🏛️ Candidate System Architecture Diagram</h4>
                      <span className="tool-badge">Mermaid Flowchart</span>
                    </div>
                    {activeDiagram ? (
                      <div className="architecture-diagram-viewer">
                        <div className="diagram-title">{activeDiagram.title}</div>
                        <div className="diagram-nodes-grid">
                          {activeDiagram.nodes?.map((node: any) => (
                            <div key={node.id} className={`arch-node-badge ${node.type}`}>
                              <span className="arch-node-icon">
                                {node.type === 'database' ? '💾' : node.type === 'cache' ? '⚡' : node.type === 'queue' ? '📬' : node.type === 'client' ? '💻' : node.type === 'proxy' ? '🛡️' : '⚙️'}
                              </span>
                              <span className="arch-node-label">{node.label}</span>
                            </div>
                          ))}
                        </div>
                        <pre className="mermaid-code-block"><code>{activeDiagram.mermaid_syntax}</code></pre>
                      </div>
                    ) : (
                      <div className="empty-tool-state">
                        <p>No active architecture diagram generated yet. The AI interviewer will generate one dynamically during the System Design stage.</p>
                      </div>
                    )}
                  </div>

                  {/* Python Code Sandbox Runner */}
                  <div className="tool-card">
                    <div className="tool-card-header">
                      <h4>🐍 Candidate Python Code Sandbox</h4>
                      <button className="btn btn-secondary btn-sm" onClick={handleRunSandboxCode} disabled={isExecutingCode}>
                        {isExecutingCode ? 'Running...' : '▶ Run Sandbox Code'}
                      </button>
                    </div>
                    <textarea
                      className="sandbox-code-editor"
                      value={sandboxCode}
                      onChange={(e) => setSandboxCode(e.target.value)}
                      rows={5}
                    />
                    {sandboxOutput && (
                      <div className="sandbox-output-console">
                        <div className="console-header">
                          <span>Execution Console (exit code: {sandboxOutput.exit_code})</span>
                          <span>{sandboxOutput.execution_time_ms}ms</span>
                        </div>
                        {sandboxOutput.stdout && <pre className="stdout-text">{sandboxOutput.stdout}</pre>}
                        {sandboxOutput.stderr && <pre className="stderr-text">⚠️ {sandboxOutput.stderr}</pre>}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* Benchmark Suite Tab */
                <div className="benchmark-tab-content">
                  <div className="benchmark-hero">
                    <div>
                      <h4>🧪 AI Evaluator Calibration Benchmark</h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Evaluates scoring calibration (MAE) and red flag detection accuracy against human-graded golden samples.
                      </p>
                    </div>
                    <button className="btn btn-primary btn-sm" onClick={handleRunBenchmark} disabled={isRunningBenchmark}>
                      {isRunningBenchmark ? 'Running Suite...' : '⚡ Run Evaluation Benchmark'}
                    </button>
                  </div>

                  {benchmarkData && (
                    <div className="benchmark-metrics-grid">
                      <div className="benchmark-metric-card">
                        <div className="metric-num">{benchmarkData.mean_absolute_error.toFixed(2)}</div>
                        <div className="metric-lbl">Mean Absolute Error (MAE)</div>
                      </div>
                      <div className="benchmark-metric-card">
                        <div className="metric-num">{benchmarkData.accuracy_within_half_point_pct}%</div>
                        <div className="metric-lbl">Score Calibration (±0.8 pts)</div>
                      </div>
                      <div className="benchmark-metric-card">
                        <div className="metric-num">{Math.round(benchmarkData.red_flag_precision * 100)}%</div>
                        <div className="metric-lbl">Red Flag Precision</div>
                      </div>
                      <div className="benchmark-metric-card">
                        <div className="metric-num">{Math.round(benchmarkData.red_flag_recall * 100)}%</div>
                        <div className="metric-lbl">Red Flag Recall</div>
                      </div>
                    </div>
                  )}

                  {benchmarkData?.sample_results && (
                    <div className="benchmark-samples-table">
                      <h5>Golden Calibration Dataset ({benchmarkData.sample_results.length} samples)</h5>
                      <table className="benchmark-table">
                        <thead>
                          <tr>
                            <th>Sample ID</th>
                            <th>Expected Score</th>
                            <th>Predicted Score</th>
                            <th>Error</th>
                            <th>Red Flag</th>
                          </tr>
                        </thead>
                        <tbody>
                          {benchmarkData.sample_results.map((res: any) => (
                            <tr key={res.sample_id}>
                              <td><code>{res.sample_id}</code></td>
                              <td>⭐ {res.expected_score.toFixed(1)}</td>
                              <td>⭐ {res.predicted_score.toFixed(1)}</td>
                              <td><span className={`error-tag ${res.absolute_error < 0.5 ? 'good' : 'warn'}`}>±{res.absolute_error.toFixed(2)}</span></td>
                              <td>{res.detected_red_flag ? `🚩 ${res.detected_red_flag}` : '✓ Clean'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Room Body */}
      {!isConnected ? (
        <div className="connection-setup-card">
          <div className="setup-icon">🎙️</div>
          <h2>Launch Interview Session</h2>
          <p className="setup-description">
            Connecting to LiveKit WebRTC channel with Evidence-Based Evaluation and red flag detection.
          </p>

          <div className="form-group">
            <label>Candidate Name</label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="input-field"
              placeholder="e.g. Alex Chen"
            />
          </div>

          <div className="form-group">
            <label>Interview Room ID</label>
            <input
              type="text"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              className="input-field"
              placeholder="e.g. sde-interview-01"
            />
          </div>

          <button className="btn btn-primary btn-full" onClick={handleConnect}>
            <span>Connect & Begin Interview</span>
            <span>→</span>
          </button>
        </div>
      ) : (
        <div className="active-room-layout">
          {/* Visualizer & Latency Telemetry HUD */}
          <div className="agent-visualizer-card">
            <div className="status-row">
              {/* VAD State Pill */}
              <div className={`vad-state-pill ${vadState}`}>
                {vadState === 'speaking' && '🟢 Candidate Speaking'}
                {vadState === 'paused' && '🟡 Thinking Pause'}
                {vadState === 'endpoint' && '🟣 Turn Endpoint'}
                {vadState === 'idle' && '⚪ Ready / Listening'}
              </div>

              {/* Adaptive Strategy Pill */}
              {adaptiveStrategy && (
                <div className="adaptive-strategy-pill">
                  {adaptiveStrategy}
                </div>
              )}

              {/* Turn Score Pill */}
              {latestTurnScore !== null && (
                <div className="turn-score-pill">
                  ⭐ Score: {latestTurnScore.toFixed(1)}/5.0
                </div>
              )}

              {/* RAG Context Pill */}
              {activeRagSnippet && (
                <div className="rag-context-hud-pill" title={activeRagSnippet}>
                  📚 RAG: {activeRagSnippet.split(':')[0]}
                </div>
              )}

              {/* Working Memory Claims Pill */}
              {memoryClaimsCount > 0 && (
                <div className="memory-claims-hud-pill">
                  🧠 {memoryClaimsCount} Claim{memoryClaimsCount > 1 ? 's' : ''}
                </div>
              )}

              {/* Language Pill */}
              {detectedLanguage && (
                <div className="language-hud-pill">
                  🌐 {detectedLanguage}
                </div>
              )}

              {/* A/B Experiment Variant Pill */}
              {assignedVariants && (
                <div className="experiment-hud-pill" title={JSON.stringify(assignedVariants)}>
                  🧪 A/B: {assignedVariants.exp_llm_model ? assignedVariants.exp_llm_model.replace('control_', '').replace('treatment_', '') : 'Active'}
                </div>
              )}

              {/* Red Flag Badge if detected */}
              {evidenceReport?.red_flags && evidenceReport.red_flags.length > 0 && (
                <div className="red-flag-hud-pill">
                  🚩 {evidenceReport.red_flags.length} Flag{evidenceReport.red_flags.length > 1 ? 's' : ''}
                </div>
              )}

              {/* Barge-In Action Button */}
              {agentStatus === 'speaking' && (
                <button className="btn-barge-in" onClick={handleInterrupt}>
                  🛑 Interrupt Agent
                </button>
              )}
            </div>

            <div className={`waveform-visualizer ${agentStatus}`}>
              <div className="bar bar-1"></div>
              <div className="bar bar-2"></div>
              <div className="bar bar-3"></div>
              <div className="bar bar-4"></div>
              <div className="bar bar-5"></div>
              <div className="bar bar-6"></div>
              <div className="bar bar-7"></div>
            </div>
            <div className="agent-state-label">
              {agentStatus === 'listening' && '👂 Listening to candidate...'}
              {agentStatus === 'thinking' && '⚡ Extracting evidence quotes & verifying technical claims...'}
              {agentStatus === 'speaking' && '🗣️ Agent speaking (Candidate can interrupt anytime)...'}
              {agentStatus === 'idle' && 'Ready'}
            </div>

            {/* Live Streaming, VAD, & Barge-In Latency HUD */}
            {activeMetrics && (
              <div className="live-latency-hud">
                <div className="hud-metric">
                  <span className="hud-label">LLM TTFT</span>
                  <span className="hud-val ttft">{activeMetrics.llm_ttft_ms ?? 0}ms</span>
                </div>
                <div className="hud-metric">
                  <span className="hud-label">TTS TTFA</span>
                  <span className="hud-val ttfa">{activeMetrics.tts_ttfa_ms ?? 0}ms</span>
                </div>
                {activeMetrics.pause_count !== undefined && (
                  <div className="hud-metric">
                    <span className="hud-label">Pauses</span>
                    <span className="hud-val" style={{ color: 'var(--accent-yellow)' }}>{activeMetrics.pause_count}</span>
                  </div>
                )}
                {activeMetrics.interrupted && (
                  <div className="hud-metric">
                    <span className="hud-label">Cutoff</span>
                    <span className="hud-val" style={{ color: 'var(--accent-red)' }}>{activeMetrics.cancellation_latency_ms ?? 0}ms</span>
                  </div>
                )}
                <div className="hud-metric">
                  <span className="hud-label">Perceived</span>
                  <span className="hud-val perceived">{activeMetrics.total_perceived_ms ?? activeMetrics.total_latency_ms ?? 0}ms</span>
                </div>
              </div>
            )}

            {/* Waterfall Latency Timeline Breakdown */}
            {activeMetrics && (
              <div className="waterfall-latency-bar">
                <div className="waterfall-segment stt" style={{ flex: Math.max(1, activeMetrics.stt_latency_ms ?? 50) }} title={`STT: ${activeMetrics.stt_latency_ms ?? 50}ms`}>
                  STT
                </div>
                <div className="waterfall-segment llm" style={{ flex: Math.max(1, activeMetrics.llm_ttft_ms ?? 150) }} title={`LLM TTFT: ${activeMetrics.llm_ttft_ms ?? 150}ms`}>
                  TTFT
                </div>
                <div className="waterfall-segment tts" style={{ flex: Math.max(1, activeMetrics.tts_ttfa_ms ?? 120) }} title={`TTS TTFA: ${activeMetrics.tts_ttfa_ms ?? 120}ms`}>
                  TTFA
                </div>
              </div>
            )}

            {/* VAD Sensitivity Control Slider */}
            <div className="vad-settings-bar">
              <label className="vad-slider-label">
                <span>VAD Silence Threshold: <strong>{silenceThresholdMs}ms</strong></span>
                <input
                  type="range"
                  min="400"
                  max="1600"
                  step="100"
                  value={silenceThresholdMs}
                  onChange={(e) => setSilenceThresholdMs(Number(e.target.value))}
                  className="vad-slider"
                />
              </label>
            </div>

            {sessionToken && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                LiveKit Host: {livekitUrl} • Session ID: {activeSession?.session_id || roomName} • Stage: {currentStage.toUpperCase()}
              </div>
            )}
          </div>

          {/* Transcript Feed */}
          <div className="transcript-feed">
            {messages.map((msg) => (
              <div key={msg.id} className={`transcript-bubble ${msg.role}`}>
                <div className="bubble-header">
                  <span className="bubble-author">
                    {msg.role === 'candidate' ? `🧑 ${candidateName}` : '🤖 AI Interviewer'}
                  </span>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    {msg.evaluation && (
                      <span className="bubble-score-tag">
                        ⭐ {msg.evaluation.overall_score.toFixed(1)}
                      </span>
                    )}
                    {msg.adaptiveStrategy && (
                      <span className="bubble-strategy-tag">{msg.adaptiveStrategy}</span>
                    )}
                    {msg.stage && <span className="bubble-stage-tag">{msg.stage}</span>}
                    <span className="bubble-time">{msg.timestamp}</span>
                  </div>
                </div>
                <div className="bubble-content">
                  {msg.text}
                  {msg.isStreaming && <span className="typing-cursor">▌</span>}
                  {msg.wasInterrupted && <span className="interrupted-tag"> [Interrupted]</span>}
                </div>
                {msg.metrics && (
                  <div className="latency-badge-row">
                    {msg.metrics.llm_ttft_ms !== undefined && (
                      <span className="latency-badge">TTFT: {msg.metrics.llm_ttft_ms}ms</span>
                    )}
                    {msg.metrics.tts_ttfa_ms !== undefined && (
                      <span className="latency-badge">TTFA: {msg.metrics.tts_ttfa_ms}ms</span>
                    )}
                    {msg.metrics.interrupted && (
                      <span className="latency-badge" style={{ color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.4)' }}>
                        🛑 Cutoff: {msg.metrics.cancellation_latency_ms}ms
                      </span>
                    )}
                    <span className="latency-badge total">
                      Total: {msg.metrics.total_perceived_ms ?? msg.metrics.total_turn_ms ?? msg.metrics.total_latency_ms}ms
                    </span>
                  </div>
                )}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>

          {/* Interaction & Mic Control Bar */}
          <div className="voice-controls-bar">
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                className={`mic-toggle-btn ${isMuted ? 'muted' : 'active'}`}
                onClick={() => setIsMuted(!isMuted)}
                title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
              >
                {isMuted ? '🔇 Muted' : '🎙️ Mic Active'}
              </button>

              {agentStatus === 'speaking' && (
                <button className="btn-barge-in-sm" onClick={handleInterrupt}>
                  🛑 Barge-in
                </button>
              )}
            </div>

            <div className="quick-replies">
              <button
                className="chip-btn"
                onClick={() => {
                  handleInterrupt();
                  handleSendTurn('In our high-throughput cluster, we debugged a production deadlock caused by row locks, so we migrated to optimistic versioning with retry backoffs. We accepted occasional rollback latency as a trade-off for eliminating lock contention.');
                }}
                disabled={isProcessing}
              >
                "Strong: Optimistic locking with prod trade-offs"
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSendTurn('We had zero latency and 100% ACID consistency across microservices because network never fails.')}
                disabled={isProcessing}
              >
                "Red Flag: Zero latency & reliable network"
              </button>
            </div>

            <form
              className="voice-input-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendTurn();
              }}
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Speak, interrupt, or type technical response..."
                className="input-field voice-input"
                disabled={isProcessing}
              />
              <button type="submit" className="btn btn-primary btn-send" disabled={isProcessing || !inputText.trim()}>
                {isProcessing ? '⚡ Streaming...' : 'Send Turn'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
