import React, { useState, useEffect, useRef } from 'react';

interface VoiceMetrics {
  stt_latency_ms: number;
  llm_latency_ms: number;
  tts_latency_ms: number;
  total_latency_ms: number;
}

interface TranscriptMessage {
  id: string;
  role: 'candidate' | 'interviewer';
  text: string;
  audioBase64?: string;
  metrics?: VoiceMetrics;
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
  const [inputText, setInputText] = useState('');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string>('');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [agentStatus, setAgentStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  // Connect to LiveKit session via Token API
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
        text: `Hello ${candidateName}! Welcome to your technical interview. Let's begin. Could you start by introducing yourself and your experience?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      setMessages([initialGreeting]);
    } catch (err: any) {
      console.error('Connection error:', err);
      setErrorMsg(err.message || 'Failed to connect to voice session');
    }
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    setSessionToken(null);
    setAgentStatus('idle');
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

  // Submit voice / text turn to backend Voice Pipeline
  const handleSendTurn = async (customText?: string) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim() || isProcessing) return;

    setErrorMsg(null);
    setIsProcessing(true);
    setAgentStatus('thinking');

    const userMsgId = `user-${Date.now()}`;
    const userMsg: TranscriptMessage = {
      id: userMsgId,
      role: 'candidate',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

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

      const agentMsg: TranscriptMessage = {
        id: `agent-${Date.now()}`,
        role: 'interviewer',
        text: data.response_text,
        audioBase64: data.audio_base64,
        metrics: data.metrics,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };

      setMessages((prev) => [...prev, agentMsg]);

      // Trigger audio playback
      if (data.audio_base64) {
        playAudio(data.audio_base64);
      }

      // Reset to listening after speaking
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
              {isConnected ? `Connected as ${candidateName} • ${agentStatus.toUpperCase()}` : 'LiveKit WebRTC Voice Pipeline v0.2.0'}
            </span>
          </div>
        </div>

        <div className="room-actions">
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
            Test the realtime STT → LLM → TTS pipeline with LiveKit token authentication and latency tracking.
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
          {/* Visualizer & Agent Status Bar */}
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
              {agentStatus === 'thinking' && '🧠 Agent generating technical response...'}
              {agentStatus === 'speaking' && '🗣️ Agent speaking via TTS...'}
              {agentStatus === 'idle' && 'Ready'}
            </div>
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
                <div className="bubble-content">{msg.text}</div>
                {msg.metrics && (
                  <div className="latency-badge-row">
                    <span className="latency-badge">STT: {msg.metrics.stt_latency_ms}ms</span>
                    <span className="latency-badge">LLM: {msg.metrics.llm_latency_ms}ms</span>
                    <span className="latency-badge">TTS: {msg.metrics.tts_latency_ms}ms</span>
                    <span className="latency-badge total">Total: {msg.metrics.total_latency_ms}ms</span>
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
                onClick={() => handleSendTurn('I have 3 years of experience in backend development with Python and PostgreSQL.')}
                disabled={isProcessing}
              >
                "3 yrs Python / Postgres experience"
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSendTurn('In distributed systems, the CAP theorem balances consistency, availability, and partition tolerance.')}
                disabled={isProcessing}
              >
                "Explain CAP theorem"
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
                placeholder="Type or speak candidate response..."
                className="input-field voice-input"
                disabled={isProcessing}
              />
              <button type="submit" className="btn btn-primary btn-send" disabled={isProcessing || !inputText.trim()}>
                {isProcessing ? '...' : 'Send Turn'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
