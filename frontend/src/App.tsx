import { useEffect, useState } from 'react';

interface HealthStatus {
  status: string;
  project: string;
  environment: string;
  version: string;
}

function App() {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [demoActive, setDemoActive] = useState<boolean>(false);

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
    // Poll health status every 10 seconds
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [API_URL]);

  const handleStartDemo = () => {
    setDemoActive(true);
    setTimeout(() => setDemoActive(false), 4000);
  };

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <header className="navbar">
        <div className="logo">
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

      {/* Hero Section */}
      <main className="main-content">
        <section className="hero-section">
          <div className="badge">Project Foundation • Phase 0</div>
          <h1 className="hero-title">
            Realtime Voice AI<br />Technical Interviewer
          </h1>
          <p className="hero-subtitle">
            VoiceHire conducts adaptive technical interviews, challenging software developers with 
            conversational depth, natural interruptions, and objective evidence-based evaluations.
          </p>

          <div className="btn-container">
            <button className="btn btn-primary" onClick={handleStartDemo}>
              <span>Start Interview</span>
              <span>→</span>
            </button>
            <a 
              href="https://github.com/livekit/agents" 
              target="_blank" 
              rel="noopener noreferrer" 
              style={{ textDecoration: 'none' }}
            >
              <button className="btn btn-secondary">Powered by LiveKit</button>
            </a>
          </div>

          {demoActive && (
            <div style={{
              margin: '20px auto 0 auto',
              padding: '16px 24px',
              borderRadius: '12px',
              backgroundColor: 'rgba(124, 58, 237, 0.15)',
              border: '1px solid rgba(124, 58, 237, 0.3)',
              color: '#c084fc',
              fontSize: '15px',
              fontWeight: 500,
              maxWidth: '500px',
              animation: 'fade-in-up 0.3s ease-out'
            }}>
              🚀 <strong>Phase 0 is active!</strong> The Voice Pipeline and realtime interview logic will be unlocked in the upcoming Phase 1 (v0.2.0) and Phase 2 (v0.3.0).
            </div>
          )}
        </section>

        {/* Feature Highlights / Roadmap */}
        <section className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎙️</div>
            <h3 className="feature-title">Voice Pipeline</h3>
            <p className="feature-desc">
              Fast, high-fidelity WebRTC audio connection to STT, LLM, and TTS adapters for low-latency feedback.
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
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} VoiceHire. Built with FastAPI, Next/React, & LiveKit.</p>
      </footer>
    </div>
  );
}

export default App;
