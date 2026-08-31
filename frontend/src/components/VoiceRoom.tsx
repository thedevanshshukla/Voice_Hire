import React, { useState, useEffect, useRef } from 'react';

interface VoiceMetrics {
  stt_latency_ms?: number;
  llm_ttft_ms?: number;
  llm_total_ms?: number;
  tts_ttfa_ms?: number;
  tts_total_ms?: number;
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
  timestamp: string;
}

interface VoiceRoomProps {
  apiUrl: string;
  onClose?: () => void;
}

export const VoiceRoom: React.FC<VoiceRoomProps> = ({ apiUrl, onClose }) => {
  const [roomName, setRoomName] = useState('interview-session-01');
  const [candidateName, setCandidateName] = useState('Candidate');
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useStreamingMode, setUseStreamingMode] = useState(true);
  const [inputText, setInputText] = useState('');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string>('');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [agentStatus, setAgentStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeMetrics, setActiveMetrics] = useState<VoiceMetrics | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  // Connect to LiveKit session via Token API & setup WebSocket for streaming
  const handleConnect = async () => {
    setErrorMsg(null);
    try {
      const res = await fetch(`${apiUrl}/api/voice/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: roomName,
          identity: `candidate-${Date.now()}`,
          name: candidateName
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

      // Initial greeting message
      const initialGreeting: TranscriptMessage = {
        id: 'msg-0',
        role: 'interviewer',
        text: `Hello ${candidateName}! Welcome to your technical interview. Let's begin. Could you start by introducing yourself and your background?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      setMessages([initialGreeting]);
    } catch (err: any) {
      console.error('Connection error:', err);
      setErrorMsg(err.message || 'Failed to connect to voice session');
    }
  };

  const handleDisconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setSessionToken(null);
    setAgentStatus('idle');
    setActiveMetrics(null);
  };

  // Play audio from base64 string
  const playAudio = (base64Audio: string) => {
    try {
      const snd = new Audio(`data:audio/wav;base64,${base64Audio}`);
      snd.play();
    } catch (err) {
      console.error('Error playing audio:', err);
    }
  };

  // Process streaming turn over WebSocket
  const handleSendStreamingTurn = async (textToSend: string) => {
    const wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/voice/stream/ws';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    const agentMsgId = `agent-${Date.now()}`;
    let fullAgentText = '';

    ws.onopen = () => {
      setAgentStatus('thinking');
      const historyPayload = messages.map((m) => ({
        role: m.role === 'candidate' ? 'user' : 'assistant',
        content: m.text
      }));

      // Add temporary streaming agent message
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
        history: historyPayload
      }));
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.event_type === 'token') {
          fullAgentText += payload.text;
          setAgentStatus('speaking');
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMsgId ? { ...msg, text: fullAgentText } : msg
            )
          );
        } else if (payload.event_type === 'audio_chunk' && payload.audio_chunk_b64) {
          playAudio(payload.audio_chunk_b64);
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
    };
  };

  // Submit voice / text turn to backend
  const handleSendTurn = async (customText?: string) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim() || isProcessing) return;

    setErrorMsg(null);
    setIsProcessing(true);

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
      }, 2000);
    } catch (err: any) {
      console.error('Turn error:', err);
      setErrorMsg(err.message || 'Error processing speech turn');
      setAgentStatus('listening');
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
            <h3 className="room-title">
              {isConnected ? `Room: ${roomName}` : 'Technical Interview Session'}
            </h3>
            <span className="room-subtitle">
              {isConnected ? `Connected as ${candidateName} • ${agentStatus.toUpperCase()}` : 'LiveKit WebRTC Streaming Voice Pipeline v0.3.0'}
            </span>
          </div>
        </div>

        <div className="room-actions">
          {isConnected && (
            <div className="mode-toggle">
              <label className="switch-label">
                <input
                  type="checkbox"
                  checked={useStreamingMode}
                  onChange={(e) => setUseStreamingMode(e.target.checked)}
                />
                <span>⚡ Realtime Stream</span>
              </label>
            </div>
          )}
          {isConnected ? (
            <button className="btn btn-disconnect" onClick={handleDisconnect}>
              Leave Session
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

      {/* Main Room Body */}
      {!isConnected ? (
        <div className="connection-setup-card">
          <div className="setup-icon">🎙️</div>
          <h2>Join Voice Interview Session</h2>
          <p className="setup-description">
            Experience ultra low-latency streaming Voice AI with LiveKit token authentication, TTFT/TTFA telemetry, and natural conversational flow.
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
            <span>Initialize & Connect Voice Room</span>
            <span>→</span>
          </button>
        </div>
      ) : (
        <div className="active-room-layout">
          {/* Visualizer & Latency Telemetry HUD */}
          <div className="agent-visualizer-card">
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
              {agentStatus === 'speaking' && '🗣️ Agent speaking via streaming audio...'}
              {agentStatus === 'idle' && 'Ready'}
            </div>

            {/* Live Streaming Latency HUD */}
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
                <div className="hud-metric">
                  <span className="hud-label">Perceived Turnaround</span>
                  <span className="hud-val perceived">{activeMetrics.total_perceived_ms ?? activeMetrics.total_latency_ms ?? 0}ms</span>
                </div>
              </div>
            )}

            {sessionToken && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                LiveKit Host: {livekitUrl} • Session Auth: JWT Token Active
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
                </div>
                {msg.metrics && (
                  <div className="latency-badge-row">
                    {msg.metrics.llm_ttft_ms !== undefined && (
                      <span className="latency-badge">TTFT: {msg.metrics.llm_ttft_ms}ms</span>
                    )}
                    {msg.metrics.tts_ttfa_ms !== undefined && (
                      <span className="latency-badge">TTFA: {msg.metrics.tts_ttfa_ms}ms</span>
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
            <button
              className={`mic-toggle-btn ${isMuted ? 'muted' : 'active'}`}
              onClick={() => setIsMuted(!isMuted)}
              title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
            >
              {isMuted ? '🔇 Muted' : '🎙️ Mic Active'}
            </button>

            <div className="quick-replies">
              <button
                className="chip-btn"
                onClick={() => handleSendTurn('I specialize in distributed backend microservices using Python and Redis.')}
                disabled={isProcessing}
              >
                "Distributed Python & Redis experience"
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSendTurn('How does LiveKit WebRTC handle packet loss and jitter buffer during audio streaming?')}
                disabled={isProcessing}
              >
                "LiveKit WebRTC packet loss question"
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
                placeholder="Speak or type technical response..."
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
