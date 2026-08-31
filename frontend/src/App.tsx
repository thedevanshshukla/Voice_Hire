import { useEffect, useState } from 'react';
import { VoiceRoom } from './components/VoiceRoom';

interface HealthStatus {
  status: string;
  project: string;
  environment: string;
  version: string;
  providers?: {
    stt: string;
    llm: string;
    tts: string;
  };
}

function App() {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [isVoiceRoomOpen, setIsVoiceRoomOpen] = useState<boolean>(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) {
          throw new Error('Health check failed');
        }
        const data = await response.json();
        setBackendHealth(data);
        setError(false);
      } catch (err) {
        console.error('Error fetching backend health:', err);
        setError(true);
        setBackendHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [API_URL]);

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <header className="navbar">
        <div className="logo" onClick={() => setIsVoiceRoomOpen(false)} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">VH</div>
          <span>VoiceHire</span>
        </div>
        <div className="status-badge">
          <span 
            className={`status-dot ${error ? 'disconnected' : 'healthy'}`}
            title={error ? 'Disconnected from backend API' : 'Connected to backend API'}
          />
          <span>
            {loading ? 'Checking status...' : error ? 'API Offline' : `API Online v${backendHealth?.version}`}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {isVoiceRoomOpen ? (
          <VoiceRoom apiUrl={API_URL} onClose={() => setIsVoiceRoomOpen(false)} />
        ) : (
          <>
            <section className="hero-section">
              <div className="badge">Phase 1 Active • Basic Voice Pipeline (v0.2.0)</div>
              <h1 className="hero-title">
                Realtime Voice AI<br />Technical Interviewer
              </h1>
              <p className="hero-subtitle">
                VoiceHire conducts adaptive technical interviews, challenging software developers with 
                conversational depth, natural interruptions, and objective evidence-based evaluations.
              </p>

              <div className="btn-container">
                <button className="btn btn-primary" onClick={() => setIsVoiceRoomOpen(true)}>
                  <span>Launch Voice Interview</span>
                  <span>🎙️</span>
                </button>
                <a 
                  href="https://livekit.io" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  style={{ textDecoration: 'none' }}
                >
                  <button className="btn btn-secondary">Powered by LiveKit</button>
                </a>
              </div>

              {/* Providers Status Card */}
              {backendHealth?.providers && (
                <div className="providers-info-banner">
                  <span className="provider-tag">STT: <strong>{backendHealth.providers.stt}</strong></span>
                  <span className="provider-tag">LLM: <strong>{backendHealth.providers.llm}</strong></span>
                  <span className="provider-tag">TTS: <strong>{backendHealth.providers.tts}</strong></span>
                </div>
              )}
            </section>

            {/* Feature Highlights / Roadmap */}
            <section className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🎙️</div>
                <h3 className="feature-title">Voice Pipeline (v0.2.0)</h3>
                <p className="feature-desc">
                  Fast WebRTC audio connection and provider abstractions for STT, LLM, and TTS with round-trip latency tracking.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">Natural Turn Taking</h3>
                <p className="feature-desc">
                  Distinguishes between a natural candidate pause and completion of an answer using VAD and Turn Detection.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🛑</div>
                <h3 className="feature-title">Barge-in Support</h3>
                <p className="feature-desc">
                  Interrupter agent stops speaking immediately upon candidate barge-in, cancelling active audio tracks seamlessly.
                </p>
              </div>
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} VoiceHire. Built with FastAPI, Next/React, & LiveKit.</p>
      </footer>
    </div>
  );
}

export default App;
