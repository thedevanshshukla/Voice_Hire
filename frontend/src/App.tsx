import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AuthView } from './components/AuthView';
import { DashboardView } from './components/DashboardView';
import { InterviewSetup } from './components/InterviewSetup';
import { VoiceRoom } from './components/VoiceRoom';
import { ReportView } from './components/ReportView';

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

// Protected Route Guard requiring active authentication
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-state">Checking session authorization...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  return <>{children}</>;
};

const NavigationBar: React.FC<{ backendHealth: HealthStatus | null; loading: boolean; error: boolean }> = ({
  backendHealth: _backendHealth,
  loading,
  error
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="navbar">
      <div className="logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
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

        {isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Link to="/dashboard" className="btn btn-secondary btn-sm">
              Dashboard
            </Link>
            <div className="user-profile-badge">
              <span className="user-initial">{user?.full_name?.charAt(0).toUpperCase() || 'U'}</span>
              <span className="user-name">{user?.full_name}</span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Sign Out
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '10px' }}>
            <Link to="/auth" className="btn btn-secondary btn-sm">
              Sign In
            </Link>
            <Link to="/auth" className="btn btn-primary btn-sm">
              Create Account
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

const HomePage: React.FC<{ backendHealth: HealthStatus | null }> = ({ backendHealth }) => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
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
          {isAuthenticated ? (
            <>
              <button className="btn btn-primary" onClick={() => navigate('/setup')}>
                <span>Configure & Launch Assessment</span>
                <span>→</span>
              </button>
              <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
                <span>Assessment Dashboard</span>
                <span>→</span>
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-primary" onClick={() => navigate('/auth')}>
                <span>Sign In to Begin Assessment</span>
                <span>→</span>
              </button>
              <button className="btn btn-secondary" onClick={() => navigate('/auth')}>
                <span>Create an Account</span>
                <span>→</span>
              </button>
            </>
          )}
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
  );
};

function App() {
  const [backendHealth, setBackendHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

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
    <AuthProvider apiUrl={API_URL}>
      <BrowserRouter>
        <div className="app-container">
          <NavigationBar backendHealth={backendHealth} loading={loading} error={error} />

          <main className="main-content">
            <Routes>
              <Route path="/" element={<HomePage backendHealth={backendHealth} />} />
              <Route path="/auth" element={<AuthView apiUrl={API_URL} />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardView apiUrl={API_URL} />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/setup"
                element={
                  <ProtectedRoute>
                    <InterviewSetup apiUrl={API_URL} />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/interview/:sessionId"
                element={
                  <ProtectedRoute>
                    <VoiceRoom apiUrl={API_URL} />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/report/:sessionId"
                element={
                  <ProtectedRoute>
                    <ReportView apiUrl={API_URL} />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>

          <footer className="footer">
            <div>VoiceHire Enterprise Assessment Platform</div>
            <div style={{ color: 'var(--text-muted)' }}>
              Production Ready • WebRTC Audio Engine
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
