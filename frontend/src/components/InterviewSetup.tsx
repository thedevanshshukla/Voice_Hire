import React, { useState, useEffect } from 'react';

export interface InterviewConfig {
  role: string;
  experience_level: string;
  job_description?: string;
  topics: string[];
  duration_minutes: number;
  language: string;
}

export interface InterviewSession {
  session_id: string;
  candidate_id: string;
  candidate_name: string;
  config: InterviewConfig;
  status: string;
  created_at: string;
  turn_count: number;
}

interface InterviewSetupProps {
  apiUrl: string;
  onStartSession: (session: InterviewSession) => void;
}

const ROLES = [
  { id: 'Backend Engineer', title: 'Backend Engineer', icon: '⚙️', desc: 'Databases, APIs, concurrency, and scalable services.' },
  { id: 'Frontend Engineer', title: 'Frontend Engineer', icon: '🎨', desc: 'React, performance, state management, and modern Web APIs.' },
  { id: 'Fullstack Engineer', title: 'Fullstack Engineer', icon: '🚀', desc: 'End-to-end web architectures, backend logic, and user interfaces.' },
  { id: 'DevOps / SRE Engineer', title: 'DevOps / SRE', icon: '☁️', desc: 'CI/CD, Kubernetes, cloud infrastructure, and site reliability.' },
  { id: 'Distributed Systems Architect', title: 'Systems Architect', icon: '🏛️', desc: 'High-availability, consensus, sharding, and fault tolerance.' }
];

const EXPERIENCE_LEVELS = [
  { id: 'SDE-1 (0-2 years)', label: 'SDE-1', sub: '0-2 yrs • Core Fundamentals' },
  { id: 'SDE-2 (2-5 years)', label: 'SDE-2', sub: '2-5 yrs • Practical System Depth' },
  { id: 'Senior / SDE-3 (5-8 years)', label: 'Senior', sub: '5-8 yrs • Scale & Tradeoffs' },
  { id: 'Staff / Principal (8+ years)', label: 'Staff+', sub: '8+ yrs • Architecture & Strategy' }
];

const AVAILABLE_TOPICS = [
  'DBMS & SQL',
  'Operating Systems & Concurrency',
  'Networking & Protocols',
  'System Design & Architecture',
  'Caching & Redis',
  'Distributed Systems',
  'REST & GraphQL API Design',
  'Message Queues & Event Streaming'
];

export const InterviewSetup: React.FC<InterviewSetupProps> = ({ apiUrl, onStartSession }) => {
  const [candidateName, setCandidateName] = useState('Alex Chen');
  const [selectedRole, setSelectedRole] = useState('Backend Engineer');
  const [selectedLevel, setSelectedLevel] = useState('SDE-2 (2-5 years)');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([
    'DBMS & SQL',
    'Operating Systems & Concurrency',
    'System Design & Architecture'
  ]);
  const [jobDescription, setJobDescription] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [language, setLanguage] = useState('English');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pastSessions, setPastSessions] = useState<InterviewSession[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch past sessions
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/interview/sessions`);
        if (res.ok) {
          const data = await res.json();
          setPastSessions(data);
        }
      } catch (err) {
        console.warn('Could not fetch past sessions:', err);
      }
    };
    fetchHistory();
  }, [apiUrl]);

  const toggleTopic = (topic: string) => {
    if (selectedTopics.includes(topic)) {
      if (selectedTopics.length > 1) {
        setSelectedTopics(selectedTopics.filter((t) => t !== topic));
      }
    } else {
      setSelectedTopics([...selectedTopics, topic]);
    }
  };

  const handleCreateAndLaunch = async () => {
    if (!candidateName.trim()) {
      setErrorMsg('Please enter candidate name');
      return;
    }
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const payload: InterviewConfig = {
        role: selectedRole,
        experience_level: selectedLevel,
        job_description: jobDescription.trim() || undefined,
        topics: selectedTopics,
        duration_minutes: durationMinutes,
        language
      };

      const res = await fetch(`${apiUrl}/api/interview/session?candidate_name=${encodeURIComponent(candidateName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Failed to create interview session: ${res.status}`);
      }

      const session: InterviewSession = await res.json();
      onStartSession(session);
    } catch (err: any) {
      console.error('Session creation error:', err);
      setErrorMsg(err.message || 'Error configuring interview session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="interview-setup-container">
      {/* Header bar */}
      <div className="setup-header">
        <div>
          <div className="badge">Interview Foundation v0.6.0</div>
          <h2 className="setup-title">Configure Technical Interview</h2>
          <p className="setup-subtitle">
            Tailor the AI interviewer to your exact role requirements, seniority level, and technical domains.
          </p>
        </div>

        <button 
          className="btn btn-secondary history-toggle-btn"
          onClick={() => setShowHistory(!showHistory)}
        >
          <span>📜 Past Interviews</span>
          <span className="history-count">{pastSessions.length}</span>
        </button>
      </div>

      {errorMsg && <div className="error-banner">⚠️ {errorMsg}</div>}

      {/* History Drawer */}
      {showHistory && (
        <div className="past-sessions-drawer">
          <div className="drawer-header">
            <h4>Previous Interview Sessions ({pastSessions.length})</h4>
            <button className="btn-close" onClick={() => setShowHistory(false)}>✕</button>
          </div>
          {pastSessions.length === 0 ? (
            <p className="empty-history">No previous sessions found in MongoDB.</p>
          ) : (
            <div className="history-grid">
              {pastSessions.map((s) => (
                <div 
                  key={s.session_id} 
                  className="history-card"
                  onClick={() => onStartSession(s)}
                >
                  <div className="history-card-header">
                    <span className="history-role">{s.config?.role || 'Technical Interview'}</span>
                    <span className={`history-status ${s.status}`}>{s.status}</span>
                  </div>
                  <div className="history-meta">
                    <span>🧑 {s.candidate_name}</span>
                    <span>⏱️ {s.config?.duration_minutes || 30}m</span>
                    <span>💬 {s.turn_count} turns</span>
                  </div>
                  <div className="history-topics">
                    {s.config?.topics?.slice(0, 2).map((t, idx) => (
                      <span key={idx} className="topic-tag-mini">{t}</span>
                    ))}
                    {(s.config?.topics?.length || 0) > 2 && (
                      <span className="topic-tag-mini">+{(s.config?.topics?.length || 0) - 2}</span>
                    )}
                  </div>
                  <div className="history-date">
                    {new Date(s.created_at).toLocaleDateString()} {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Setup Form */}
      <div className="setup-grid">
        {/* Left Column: Role & Level Selection */}
        <div className="setup-section">
          <div className="section-label">1. Target Engineering Role</div>
          <div className="roles-grid">
            {ROLES.map((r) => (
              <div
                key={r.id}
                className={`role-card ${selectedRole === r.id ? 'active' : ''}`}
                onClick={() => setSelectedRole(r.id)}
              >
                <div className="role-card-top">
                  <span className="role-icon">{r.icon}</span>
                  <span className="role-name">{r.title}</span>
                </div>
                <p className="role-desc">{r.desc}</p>
              </div>
            ))}
          </div>

          <div className="section-label" style={{ marginTop: '24px' }}>2. Seniority & Experience Level</div>
          <div className="levels-grid">
            {EXPERIENCE_LEVELS.map((lvl) => (
              <div
                key={lvl.id}
                className={`level-card ${selectedLevel === lvl.id ? 'active' : ''}`}
                onClick={() => setSelectedLevel(lvl.id)}
              >
                <div className="level-label">{lvl.label}</div>
                <div className="level-sub">{lvl.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Topics, Candidate info, JD */}
        <div className="setup-section">
          <div className="section-label">3. Candidate & Interview Details</div>
          <div className="form-row">
            <div className="form-group flex-1">
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
              <label>Duration</label>
              <select
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                className="input-field select-field"
              >
                <option value={15}>15 Minutes</option>
                <option value={30}>30 Minutes</option>
                <option value={45}>45 Minutes</option>
                <option value={60}>60 Minutes</option>
              </select>
            </div>
            <div className="form-group">
              <label>Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-field select-field"
              >
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
              </select>
            </div>
          </div>

          <div className="section-label" style={{ marginTop: '20px' }}>
            4. Focus Topics ({selectedTopics.length} selected)
          </div>
          <div className="topics-cloud">
            {AVAILABLE_TOPICS.map((topic) => {
              const isSelected = selectedTopics.includes(topic);
              return (
                <button
                  key={topic}
                  type="button"
                  className={`topic-chip ${isSelected ? 'selected' : ''}`}
                  onClick={() => toggleTopic(topic)}
                >
                  <span>{isSelected ? '✓' : '+'}</span>
                  <span>{topic}</span>
                </button>
              );
            })}
          </div>

          <div className="section-label" style={{ marginTop: '20px' }}>
            5. Job Description / Requirements (Optional)
          </div>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="input-field textarea-field"
            placeholder="Paste role requirements, tech stack keywords, or specific areas to probe..."
            rows={4}
          />

          <button
            className="btn btn-primary btn-full btn-launch-interview"
            onClick={handleCreateAndLaunch}
            disabled={isSubmitting}
          >
            <span>{isSubmitting ? 'Configuring Session...' : 'Start Voice Interview'}</span>
            <span>🎙️</span>
          </button>
        </div>
      </div>
    </div>
  );
};
