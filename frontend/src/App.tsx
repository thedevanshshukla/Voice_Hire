import { useEffect, useState } from 'react';
import { VoiceRoom } from './components/VoiceRoom';
import { InterviewSetup, type InterviewSession } from './components/InterviewSetup';

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
  features?: {
    streaming?: boolean;
    barge_in?: boolean;
    interview_foundation?: boolean;
  };
}

function App() {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  
  // App views: 'home' | 'setup' | 'interview'
  const [currentView, setCurrentView] = useState<'home' | 'setup' | 'interview'>('home');
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);

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

  const handleStartSession = (session: InterviewSession) => {
    setActiveSession(session);
    setCurrentView('interview');
  };

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <header className="navbar">
        <div className="logo" onClick={() => setCurrentView('home')} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">VH</div>
          <span>VoiceHire</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div className="status-badge">
            <span 
              className={`status-dot ${error ? 'disconnected' : 'healthy'}`}
              title={error ? 'Disconnected from backend API' : 'Connected to backend API'}
            />
            <span>
              {loading ? 'Checking status...' : error ? 'API Offline' : `API Online`}
            </span>
          </div>

          {currentView !== 'home' && (
            <button 
              className="btn btn-secondary btn-sm"
              onClick={() => setCurrentView(currentView === 'interview' ? 'setup' : 'home')}
            >
              {currentView === 'interview' ? 'Interview Configuration' : 'Overview'}
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {currentView === 'setup' && (
          <InterviewSetup 
            apiUrl={API_URL} 
            onStartSession={handleStartSession} 
          />
        )}

        {currentView === 'interview' && (
          <VoiceRoom 
            apiUrl={API_URL} 
            activeSession={activeSession}
            onClose={() => setCurrentView('setup')} 
          />
        )}

        {currentView === 'home' && (
          <>
            <section className="hero-section">
              <div className="badge">Autonomous Technical Assessment Platform</div>
              <h1 className="hero-title">
                Realtime Voice AI<br />Technical Interviewer
              </h1>
              <p className="hero-subtitle">
                Conduct structured, evidence-based technical interviews for software engineering roles. 
                Evaluates candidate architecture, algorithms, and systems engineering with sub-150ms conversational turn-taking and verbatim quotation scoring.
              </p>

              <div className="btn-container">
                <button className="btn btn-primary" onClick={() => setCurrentView('setup')}>
                  <span>Configure & Launch Session</span>
                  <span>→</span>
                </button>
                <button className="btn btn-secondary" onClick={() => setCurrentView('interview')}>
                  <span>Quick Start Session</span>
                  <span>→</span>
                </button>
              </div>

              {/* Providers & Capabilities Banner */}
              {backendHealth?.providers && (
                <div className="providers-info-banner">
                  <span className="provider-tag">STT: <strong>{backendHealth.providers.stt}</strong></span>
                  <span className="provider-tag">LLM: <strong>{backendHealth.providers.llm}</strong></span>
                  <span className="provider-tag">TTS: <strong>{backendHealth.providers.tts}</strong></span>
                  <span className="provider-tag">VAD: <strong>{backendHealth.providers.vad || 'energy'}</strong></span>
                  <span className="provider-tag" style={{ color: 'var(--accent-purple)' }}>Database: <strong>Connected</strong></span>
                </div>
              )}
            </section>

            {/* Feature Highlights */}
            <section className="features-grid">
              <div className="feature-card">
                <div className="feature-indicator">01</div>
                <h3 className="feature-title">Adaptive Question Engine</h3>
                <p className="feature-desc">
                  Dynamically assesses candidate depth across fundamentals, distributed systems, and system design with targeted mechanical probing.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-indicator">02</div>
                <h3 className="feature-title">Sub-150ms Conversational Turn-Taking</h3>
                <p className="feature-desc">
                  Natural full-duplex speech interaction with intelligent pause tolerance and instantaneous barge-in cutoff.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-indicator">03</div>
                <h3 className="feature-title">Evidence-Based Scorecards</h3>
                <p className="feature-desc">
                  Multi-dimensional rubric scoring supported by verbatim transcript quotes, contradiction detection, and technical red flag audits.
                </p>
              </div>
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div>VoiceHire Enterprise Assessment Platform</div>
        <div style={{ color: 'var(--text-muted)' }}>
          Production Ready • WebRTC Audio Engine
        </div>
      </footer>
    </div>
  );
}

export default App;
