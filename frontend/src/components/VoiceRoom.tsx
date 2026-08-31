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

interface TranscriptMessage {
  id: string;
  role: 'candidate' | 'interviewer';
  text: string;
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

export const VoiceRoom: React.FC<VoiceRoomProps> = ({ apiUrl, activeSession, onClose }) => {
  const [roomName, setRoomName] = useState(activeSession ? activeSession.session_id : 'interview-session-01');
  const [candidateName, setCandidateName] = useState(activeSession ? activeSession.candidate_name : 'Candidate');
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useStreamingMode, setUseStreamingMode] = useState(true);
  const [silenceThresholdMs, setSilenceThresholdMs] = useState(800);
  const [vadState, setVadState] = useState<'idle' | 'speaking' | 'paused' | 'endpoint'>('idle');
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

  // Process streaming turn over WebSocket with Interview Session Context
  const handleSendStreamingTurn = async (textToSend: string) => {
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
        
        if (payload.event_type === 'vad_event') {
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
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    if (useStreamingMode) {
      handleSendStreamingTurn(textToSend);
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

      const agentMsg: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
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
              {isConnected ? `Candidate: ${candidateName} • ${agentStatus.toUpperCase()}` : 'LiveKit WebRTC Interview v0.6.0'}
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

      {errorMsg && (
        <div className="error-banner">
          ⚠️ {errorMsg}
        </div>
      )}

      {lastInterruption && (
        <div className="interruption-banner">
          {lastInterruption}
        </div>
      )}

      {/* Main Room Body */}
      {!isConnected ? (
        <div className="connection-setup-card">
          <div className="setup-icon">🎙️</div>
          <h2>Launch Interview Session</h2>
          <p className="setup-description">
            Connecting to LiveKit WebRTC channel with MongoDB session persistence and dynamic system prompt injection.
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
              {agentStatus === 'thinking' && '⚡ Streaming LLM tokens & TTS chunks...'}
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
                LiveKit Host: {livekitUrl} • Session ID: {activeSession?.session_id || roomName} • MongoDB Synced
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
                  <span className="bubble-time">{msg.timestamp}</span>
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
                  handleSendTurn('Let me explain our database sharding and index strategy.');
                }}
                disabled={isProcessing}
              >
                "Explain database sharding"
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSendTurn('We use optimistic locking with version columns to avoid deadlocks under high concurrency.')}
                disabled={isProcessing}
              >
                "Optimistic locking concurrency"
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
