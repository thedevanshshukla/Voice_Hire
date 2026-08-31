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
    vad?: string;
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
              <div className="badge">Phase 3 Active • Natural Turn Taking (v0.4.0)</div>
              <h1 className="hero-title">
                Realtime Voice AI<br />Technical Interviewer
              </h1>
              <p className="hero-subtitle">
                VoiceHire conducts human-like conversational technical interviews, equipped with Voice Activity Detection (VAD) 
                to respect candidate thinking pauses without premature interruption.
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

              {/* Providers & VAD Status Banner */}
              {backendHealth?.providers && (
                <div className="providers-info-banner">
                  <span className="provider-tag">STT: <strong>{backendHealth.providers.stt}</strong></span>
                  <span className="provider-tag">LLM: <strong>{backendHealth.providers.llm}</strong></span>
                  <span className="provider-tag">TTS: <strong>{backendHealth.providers.tts}</strong></span>
                  <span className="provider-tag">VAD: <strong>{backendHealth.providers.vad || 'energy'}</strong></span>
                  <span className="provider-tag" style={{ color: 'var(--accent-green)' }}>⚡ Endpointing: <strong>Active</strong></span>
                </div>
              )}
            </section>

            {/* Feature Highlights / Roadmap */}
            <section className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">Natural Turn Taking (v0.4.0)</h3>
                <p className="feature-desc">
                  Intelligent endpointing engine that distinguishes between mid-sentence candidate thinking pauses and completed answers.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🎙️</div>
                <h3 className="feature-title">Adaptive VAD</h3>
                <p className="feature-desc">
                  Energy & RMS Voice Activity Detection with dynamic background noise floor tracking and configurable silence thresholds.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🛑</div>
                <h3 className="feature-title">Barge-in Support</h3>
                <p className="feature-desc">
                  Upcoming v0.5.0: Interrupter agent stops speaking immediately upon candidate barge-in, cancelling active audio tracks.
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
