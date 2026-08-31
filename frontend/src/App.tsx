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
              {loading ? 'Checking status...' : error ? 'API Offline' : `API Online v${backendHealth?.version}`}
            </span>
          </div>

          {currentView !== 'home' && (
            <button 
              className="btn btn-secondary btn-sm"
              onClick={() => setCurrentView(currentView === 'interview' ? 'setup' : 'home')}
            >
              {currentView === 'interview' ? '⚙️ Interview Setup' : '🏠 Home'}
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
              <div className="badge">Phase 5 Active • Interview Foundation (v0.6.0)</div>
              <h1 className="hero-title">
                Realtime Voice AI<br />Technical Interviewer
              </h1>
              <p className="hero-subtitle">
                Conduct structured, evidence-based technical interviews for software engineering roles. 
                Configure role seniority, probe deep technical domains, paste custom job descriptions, and persist complete interview transcripts in MongoDB.
              </p>

              <div className="btn-container">
                <button className="btn btn-primary" onClick={() => setCurrentView('setup')}>
                  <span>Configure & Launch Interview</span>
                  <span>⚙️</span>
                </button>
                <button className="btn btn-secondary" onClick={() => setCurrentView('interview')}>
                  <span>Quick Start (Default Room)</span>
                  <span>🎙️</span>
                </button>
              </div>

              {/* Providers & Capabilities Banner */}
              {backendHealth?.providers && (
                <div className="providers-info-banner">
                  <span className="provider-tag">STT: <strong>{backendHealth.providers.stt}</strong></span>
                  <span className="provider-tag">LLM: <strong>{backendHealth.providers.llm}</strong></span>
                  <span className="provider-tag">TTS: <strong>{backendHealth.providers.tts}</strong></span>
                  <span className="provider-tag">VAD: <strong>{backendHealth.providers.vad || 'energy'}</strong></span>
                  <span className="provider-tag" style={{ color: 'var(--accent-purple)' }}>🗄️ MongoDB: <strong>Synced</strong></span>
                </div>
              )}
            </section>

            {/* Feature Highlights / Roadmap */}
            <section className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🎯</div>
                <h3 className="feature-title">Interview Foundation (v0.6.0)</h3>
                <p className="feature-desc">
                  Role presets (Backend, Frontend, DevOps, Systems Architect), seniority levels (SDE-1 to Staff), custom JD parsing, and MongoDB session persistence.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🛑</div>
                <h3 className="feature-title">Barge-in Support</h3>
                <p className="feature-desc">
                  Candidate can interrupt the AI interviewer naturally at any point with sub-200ms audio cancellation and generation abortion.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3 className="feature-title">Natural Turn Taking</h3>
                <p className="feature-desc">
                  Adaptive VAD state machine protects candidate thinking pauses without premature interruptions.
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
