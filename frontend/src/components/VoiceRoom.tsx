import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { InterviewSession } from './InterviewSetup';

interface VoiceMetrics {
  ttft_ms?: number;
  ttfa_ms?: number;
  llm_ttft_ms?: number;
  tts_ttfa_ms?: number;
  stt_latency_ms?: number;
  total_perceived_ms?: number;
  pause_count?: number;
  interrupted?: boolean;
  cancellation_latency_ms?: number;
  total_latency_ms?: number;
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
  overall_confidence: string;
  confidence_score: number;
  recommendation: string;
  recommendation_reasoning: string;
  key_strengths_with_evidence: EvidenceSnippet[];
  key_weaknesses_with_evidence: EvidenceSnippet[];
  red_flags: RedFlagItem[];
}

interface TranscriptMessage {
  id: string;
  role: 'candidate' | 'interviewer' | 'system';
  text: string;
  stage?: string;
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
  { id: 'greeting', label: '1. Introduction', icon: '1' },
  { id: 'resume_deep_dive', label: '2. Project Deep Dive', icon: '2' },
  { id: 'core_concepts', label: '3. Technical Concepts', icon: '3' },
  { id: 'system_design', label: '4. System Architecture', icon: '4' },
  { id: 'candidate_questions', label: '5. Candidate Q&A', icon: '5' },
  { id: 'wrap_up', label: '6. Conclusion', icon: '6' }
];

export const VoiceRoom: React.FC<VoiceRoomProps> = ({ apiUrl, activeSession: propSession, onClose: _onClose }) => {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeSession, setActiveSession] = useState<InterviewSession | null>(propSession || null);
  const [roomName, setRoomName] = useState(paramSessionId || propSession?.session_id || 'interview-session-01');
  const [candidateName, setCandidateName] = useState(propSession?.candidate_name || user?.full_name || 'Candidate');
  
  const [isConnected, setIsConnected] = useState(false);
  const [_isMicPermissionGranted, setIsMicPermissionGranted] = useState(false);
  const [micVolumeLevel, setMicVolumeLevel] = useState<number>(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useStreamingMode] = useState(true);
  const [showEmergencyTextInput, setShowEmergencyTextInput] = useState(false);

  // Session elapsed & countdown timer
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [timerInterval, setTimerInterval] = useState<any>(null);

  const [vadState, setVadState] = useState<'idle' | 'speaking' | 'paused' | 'endpoint'>('idle');
  const [currentStage, setCurrentStage] = useState<string>('greeting');
  const [stageProgressPct, setStageProgressPct] = useState<number>(16.6);
  const [detectedLanguage, setDetectedLanguage] = useState<string>('English');

  const [sessionScorecard, setSessionScorecard] = useState<SessionScorecard | null>(null);
  const [evidenceReport, setEvidenceReport] = useState<EvidenceEvaluationReport | null>(null);
  const [showScorecardModal, setShowScorecardModal] = useState<boolean>(false);

  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [agentStatus, setAgentStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Fetch session details if routed directly via URL
  useEffect(() => {
    const fetchSession = async () => {
      const targetId = paramSessionId || propSession?.session_id;
      if (targetId && !activeSession) {
        try {
          const res = await fetch(`${apiUrl}/api/interview/session/${targetId}`);
          if (res.ok) {
            const data = await res.json();
            setActiveSession(data);
            setCandidateName(data.candidate_name);
            setRoomName(data.session_id);
            setDetectedLanguage(data.config?.language || 'English');
          }
        } catch (e) {
          console.warn('Could not fetch session details:', e);
        }
      }
    };
    fetchSession();
  }, [apiUrl, paramSessionId, propSession]);

  // Session timer hook
  useEffect(() => {
    if (isConnected) {
      const interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
      setTimerInterval(interval);
      return () => clearInterval(interval);
    } else {
      if (timerInterval) clearInterval(timerInterval);
    }
  }, [isConnected]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMicrophoneStream();
      if (wsRef.current) wsRef.current.close();
      cancelActiveAudio();
    };
  }, []);

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const cancelActiveAudio = () => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }
  };

  const stopMicrophoneStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  };

  // Request real microphone permissions and initiate Web Audio energy analyser
  const setupMicrophoneCapture = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;
      setIsMicPermissionGranted(true);

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      let isCandidateSpeaking = false;
      let lastSpeechTime = Date.now();

      const monitorAudioLevel = () => {
        if (!mediaStreamRef.current) return;
        analyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setMicVolumeLevel(normalized);

        const SPEECH_THRESHOLD = 15;
        if (normalized > SPEECH_THRESHOLD && !isMuted) {
          lastSpeechTime = Date.now();
          if (!isCandidateSpeaking) {
            isCandidateSpeaking = true;
            setVadState('speaking');
            if (agentStatus === 'speaking') {
              handleInterrupt();
            }
          }
        } else if (isCandidateSpeaking) {
          // Candidate paused or stopped
          const silenceDuration = Date.now() - lastSpeechTime;
          if (silenceDuration > 3500) {
            isCandidateSpeaking = false;
            setVadState('endpoint');
            // Auto-complete turn if candidate spoke
          } else if (silenceDuration > 800) {
            setVadState('paused');
          }
        }

        requestAnimationFrame(monitorAudioLevel);
      };

      requestAnimationFrame(monitorAudioLevel);
      return true;
    } catch (err) {
      console.error('Microphone permission error:', err);
      setErrorMsg('Microphone access was denied or is unavailable. Please grant microphone permissions to proceed.');
      setIsMicPermissionGranted(false);
      return false;
    }
  };

  const playAudio = (audioBase64: string) => {
    try {
      cancelActiveAudio();
      const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      activeAudioRef.current = audio;
      audio.onended = () => {
        setAgentStatus('listening');
        setVadState('idle');
      };
      audio.play().catch((e) => console.warn('Audio autoplay blocked or failed:', e));
    } catch (e) {
      console.error('Audio play error:', e);
    }
  };

  const handleInterrupt = () => {
    cancelActiveAudio();
    setAgentStatus('listening');
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'interrupt', reason: 'barge_in' }));
    }
  };

  const refreshScorecardAndEvidence = async () => {
    const sessId = activeSession ? activeSession.session_id : roomName;
    try {
      const [scoreRes, evRes] = await Promise.all([
        fetch(`${apiUrl}/api/interview/session/${sessId}/scorecard`),
        fetch(`${apiUrl}/api/interview/session/${sessId}/evidence-report`)
      ]);
      if (scoreRes.ok) {
        const sc = await scoreRes.json();
        setSessionScorecard(sc);
      }
      if (evRes.ok) {
        const ev = await evRes.json();
        setEvidenceReport(ev);
      }
    } catch (e) {
      console.warn('Could not fetch updated scorecard/evidence:', e);
    }
  };

  const handleConnect = async () => {
    setErrorMsg(null);
    const micOk = await setupMicrophoneCapture();
    if (!micOk) return;

    try {
      const sessId = activeSession ? activeSession.session_id : roomName;
      const response = await fetch(`${apiUrl}/api/voice/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: sessId,
          identity: `candidate-${Date.now().toString().slice(-4)}`,
          name: candidateName,
          session_id: sessId
        })
      });

      if (!response.ok) {
        throw new Error(`Token generation failed: ${response.statusText}`);
      }

      await response.json();
      setIsConnected(true);
      setAgentStatus('listening');

      // Initial welcoming greeting message
      const initialGreeting: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
        stage: 'greeting',
        text: `Hello ${candidateName}, welcome to your technical interview. I'll be guiding you through today's session. To get started, please share a brief introduction of yourself and your recent engineering projects.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      setMessages([initialGreeting]);

      // Trigger initial spoken prompt
      handleSendStreamingTurn("Hello, I am ready to begin the interview.", "init-greeting");
    } catch (err: any) {
      console.error('Connection error:', err);
      setErrorMsg(err.message || 'Failed to connect to voice room');
      setIsConnected(false);
    }
  };

  const handleDisconnect = () => {
    cancelActiveAudio();
    stopMicrophoneStream();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setAgentStatus('idle');
    setVadState('idle');

    // Route to final report view
    const sessId = activeSession ? activeSession.session_id : roomName;
    navigate(`/report/${sessId}`);
  };

  // Process streaming turn over WebSocket
  const handleSendStreamingTurn = async (textToSend: string, _userMsgId: string) => {
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
        role: m.role === 'interviewer' ? 'assistant' : 'user',
        content: m.text
      }));

      ws.send(JSON.stringify({
        action: 'turn',
        text: textToSend,
        session_id: activeSession ? activeSession.session_id : roomName,
        history: historyPayload
      }));

      // Push initial placeholder streaming bubble
      setMessages((prev) => [
        ...prev,
        {
          id: agentMsgId,
          role: 'interviewer',
          stage: currentStage,
          text: '',
          isStreaming: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        }
      ]);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.event_type === 'stage_transition') {
          setCurrentStage(payload.stage);
          setStageProgressPct(payload.progress_pct);
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
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMsgId
                ? { ...msg, text: fullAgentText + ' [interrupted]', isStreaming: false, wasInterrupted: true }
                : msg
            )
          );
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onclose = () => {
      setMessages((prev) =>
        prev.map((msg) => (msg.id === agentMsgId ? { ...msg, isStreaming: false } : msg))
      );
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setAgentStatus('listening');
      setVadState('idle');
    };
  };

  const handleSendTurn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    const currentText = inputText.trim();
    setInputText('');
    setVadState('speaking');

    const userMsgId = `user-${Date.now()}`;
    const userMsg: TranscriptMessage = {
      id: userMsgId,
      role: 'candidate',
      stage: currentStage,
      text: currentText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);

    if (useStreamingMode) {
      handleSendStreamingTurn(currentText, userMsgId);
      return;
    }

    setIsProcessing(true);
    setAgentStatus('thinking');

    try {
      const historyPayload = messages.map((m) => ({
        role: m.role === 'interviewer' ? 'assistant' : 'user',
        content: m.text
      }));

      const response = await fetch(`${apiUrl}/api/voice/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession ? activeSession.session_id : roomName,
          text: currentText,
          history: historyPayload
        })
      });

      if (!response.ok) {
        throw new Error(`Turn endpoint error: ${response.statusText}`);
      }

      const data = await response.json();
      setAgentStatus('speaking');
      setVadState('endpoint');
      if (data.detected_language) setDetectedLanguage(data.detected_language);
      if (data.current_stage) setCurrentStage(data.current_stage);
      if (data.progress_pct) setStageProgressPct(data.progress_pct);

      const agentMsg: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
        stage: data.current_stage || currentStage,
        text: data.response_text,
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
  const totalDurationSeconds = (activeSession?.config.duration_minutes || 30) * 60;
  const remainingSeconds = Math.max(0, totalDurationSeconds - elapsedSeconds);

  return (
    <div className="voice-room-container">
      {/* Header bar */}
      <div className="voice-room-header">
        <div className="room-info">
          <button className="btn-back-link" onClick={() => navigate('/dashboard')} style={{ marginRight: '12px' }}>
            ← Back to Dashboard
          </button>
          <div className={`status-indicator ${isConnected ? 'active' : 'inactive'}`} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 className="room-title">
                {activeSession ? `${activeSession.config.role} Interview` : `Interview Session`}
              </h3>
              {activeSession && (
                <span className="badge badge-sm">{activeSession.config.experience_level}</span>
              )}
            </div>
            <span className="room-subtitle">
              {isConnected ? `Candidate: ${candidateName}` : 'Ready to begin assessment'}
            </span>
          </div>
        </div>

        {/* Live Session Timer */}
        {isConnected && (
          <div className="session-timer-badge">
            <span className="timer-icon">⏱</span>
            <span>Elapsed {formatTimer(elapsedSeconds)}</span>
            <span className="timer-divider">•</span>
            <span style={{ color: remainingSeconds < 300 ? '#f87171' : 'var(--text-muted)' }}>
              {formatTimer(remainingSeconds)} Remaining
            </span>
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
              <span>Recruiter Scorecard</span>
            </button>
          )}

          {isConnected ? (
            <button className="btn btn-disconnect" onClick={handleDisconnect}>
              End Interview & View Report
            </button>
          ) : null}
        </div>
      </div>

      {/* 6-Stage Progression Timeline */}
      {isConnected && (
        <div className="stage-timeline-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '900px', margin: '0 auto 8px auto' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
              Assessment Progression
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
          {errorMsg}
        </div>
      )}

      {/* Recruiter Evaluation Modal (Protected from candidate screen) */}
      {showScorecardModal && (
        <div className="scorecard-modal-backdrop" onClick={() => setShowScorecardModal(false)}>
          <div className="scorecard-modal" onClick={(e) => e.stopPropagation()}>
            <div className="scorecard-modal-header">
              <div>
                <h3 style={{ margin: 0 }}>Recruiter Assessment Audit</h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {candidateName} • {activeSession?.config.role}
                </span>
              </div>
              <button className="btn-close" onClick={() => setShowScorecardModal(false)}>✕</button>
            </div>

            <div className="scorecard-modal-body">
              <div className="scorecard-hero">
                <div className="hero-score-val">
                  {sessionScorecard?.overall_score.toFixed(1) || '0.0'}
                  <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 5.0</span>
                </div>
                <div className="hero-verdict">
                  <div className="verdict-label">Recommendation</div>
                  <div className="verdict-title">{evidenceReport?.recommendation || sessionScorecard?.summary_verdict || 'Evaluating'}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {sessionScorecard?.total_evaluated_turns || 0} answers analyzed
                  </div>
                </div>
              </div>

              <div className="dimensions-breakdown">
                <h4>Competency Breakdown</h4>
                <div className="dim-row">
                  <div className="dim-header">
                    <span>1. Correctness</span>
                    <span className="dim-val">{sessionScorecard?.avg_correctness.toFixed(1) || '0.0'} / 5.0</span>
                  </div>
                  <div className="dim-bar-bg"><div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_correctness || 0) / 5) * 100}%` }}></div></div>
                </div>
                <div className="dim-row">
                  <div className="dim-header">
                    <span>2. Depth & Mechanics</span>
                    <span className="dim-val">{sessionScorecard?.avg_depth.toFixed(1) || '0.0'} / 5.0</span>
                  </div>
                  <div className="dim-bar-bg"><div className="dim-bar-fill" style={{ width: `${((sessionScorecard?.avg_depth || 0) / 5) * 100}%`, background: 'var(--accent-purple)' }}></div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Room Body */}
      {!isConnected ? (
        <div className="connection-setup-card">
          <h2>Ready to Begin Technical Assessment</h2>
          <p className="setup-description">
            The interview is conducted entirely over voice. Please ensure you are in a quiet environment and allow microphone access when prompted.
          </p>

          <div className="mic-check-preview-box">
            <div className="mic-check-icon">🎙</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px' }}>Microphone Permission Required</div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Your audio will be analyzed in real time for architectural and technical depth.
              </div>
            </div>
          </div>

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

          <button className="btn btn-primary btn-full btn-lg" onClick={handleConnect}>
            <span>Allow Microphone & Start Interview</span>
            <span>→</span>
          </button>
        </div>
      ) : (
        <div className="active-room-layout">
          {/* Visualizer & Mic Level HUD */}
          <div className="agent-visualizer-card">
            <div className="status-row">
              {/* Recording Indicator */}
              <div className="recording-live-pill">
                <span className="recording-dot"></span>
                <span>Recording Active</span>
              </div>

              {/* VAD State Pill */}
              <div className={`vad-state-pill ${vadState}`}>
                {vadState === 'speaking' && 'Speaking'}
                {vadState === 'paused' && 'Pausing'}
                {vadState === 'endpoint' && 'Processing Turn'}
                {vadState === 'idle' && 'Listening'}
              </div>

              {/* Language Pill */}
              <div className="language-hud-pill">
                {detectedLanguage}
              </div>

              {/* Interruption Trigger */}
              {agentStatus === 'speaking' && (
                <button className="btn-barge-in" onClick={handleInterrupt}>
                  Interrupt Agent
                </button>
              )}
            </div>

            {/* Live Audio Waveform & Mic Level Meter */}
            <div className={`waveform-visualizer ${agentStatus}`}>
              <div className="bar bar-1"></div>
              <div className="bar bar-2"></div>
              <div className="bar bar-3"></div>
              <div className="bar bar-4"></div>
              <div className="bar bar-5"></div>
              <div className="bar bar-6"></div>
              <div className="bar bar-7"></div>
            </div>

            {/* Candidate Microphone Level Meter Bar */}
            <div className="mic-level-monitor">
              <span className="mic-icon-lbl">{isMuted ? '🔇' : '🎙️'}</span>
              <div className="mic-meter-bar-bg">
                <div className="mic-meter-bar-fill" style={{ width: `${isMuted ? 0 : micVolumeLevel}%` }}></div>
              </div>
              <span className="mic-level-pct">{isMuted ? 'Muted' : `${micVolumeLevel}%`}</span>
            </div>

            <div className="agent-state-label">
              {agentStatus === 'listening' && 'Listening to candidate response... (Speak into microphone)'}
              {agentStatus === 'thinking' && 'Interviewer formulating follow-up question...'}
              {agentStatus === 'speaking' && 'Interviewer speaking (You can interrupt anytime)...'}
              {agentStatus === 'idle' && 'Connected'}
            </div>
          </div>

          {/* Conversation Transcript Stream */}
          <div className="chat-stream-card">
            <div className="chat-messages-scroll">
              {messages.map((msg) => (
                <div key={msg.id} className={`chat-bubble-wrapper ${msg.role}`}>
                  <div className={`chat-bubble ${msg.role} ${msg.isStreaming ? 'streaming' : ''} ${msg.wasInterrupted ? 'interrupted' : ''}`}>
                    <div className="bubble-header">
                      <span className="bubble-sender">
                        {msg.role === 'interviewer' ? 'AI Interviewer' : candidateName}
                      </span>
                      {msg.stage && (
                        <span className="bubble-stage-badge">
                          {msg.stage.replace('_', ' ').toUpperCase()}
                        </span>
                      )}
                      <span className="bubble-time">{msg.timestamp}</span>
                    </div>

                    <div className="bubble-content">
                      {msg.text || (msg.isStreaming ? <span className="typing-dots"><span>.</span><span>.</span><span>.</span></span> : '')}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>

            {/* Voice-Only Bottom Action Controls */}
            <div className="voice-only-controls-bar">
              <button
                type="button"
                className={`btn btn-mic ${isMuted ? 'muted' : 'active'}`}
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? '🔇 Unmute Microphone' : '🎙️ Microphone Active'}
              </button>

              <button
                type="button"
                className="emergency-text-toggle"
                onClick={() => setShowEmergencyTextInput(!showEmergencyTextInput)}
              >
                {showEmergencyTextInput ? 'Hide Text Fallback' : 'Audio Issues? Type Answer'}
              </button>
            </div>

            {/* Emergency Text Fallback Input */}
            {showEmergencyTextInput && (
              <div className="chat-input-bar">
                <form onSubmit={handleSendTurn} className="input-form">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Type candidate response here..."
                    className="input-field"
                    disabled={isProcessing}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isProcessing || !inputText.trim()}
                  >
                    <span>Send</span>
                    <span>→</span>
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
