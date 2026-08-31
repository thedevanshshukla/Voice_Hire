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

export interface KnowledgeDoc {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  role_target?: string;
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
  
  // Knowledge Base State
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDoc[]>([]);
  const [showKnowledgeDrawer, setShowKnowledgeDrawer] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocContent, setNewDocContent] = useState('');
  const [newDocCategory, setNewDocCategory] = useState('company_standards');
  const [newDocTags, setNewDocTags] = useState('idempotency, stripe, api');
  
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch past sessions & knowledge docs
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [sessRes, kbRes] = await Promise.all([
          fetch(`${apiUrl}/api/interview/sessions`),
          fetch(`${apiUrl}/api/knowledge/documents`)
        ]);
        if (sessRes.ok) {
          const data = await sessRes.json();
          setPastSessions(data);
        }
        if (kbRes.ok) {
          const kbData = await kbRes.json();
          setKnowledgeDocs(kbData);
        }
      } catch (err) {
        console.warn('Could not fetch initial setup data:', err);
      }
    };
    fetchInitialData();
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

  const handleIngestDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDocTitle.trim() || !newDocContent.trim()) return;

    try {
      const res = await fetch(`${apiUrl}/api/knowledge/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newDocTitle,
          category: newDocCategory,
          content: newDocContent,
          tags: newDocTags.split(',').map((t) => t.trim()).filter(Boolean),
          role_target: selectedRole
        })
      });
      if (res.ok) {
        const doc = await res.json();
        setKnowledgeDocs((prev) => [...prev, doc]);
        setNewDocTitle('');
        setNewDocContent('');
      }
    } catch (err) {
      console.error('Ingest error:', err);
    }
  };

  const handleCreateAndLaunch = async () => {
    if (!candidateName.trim()) {
      setErrorMsg('Please enter candidate name');
      return;
    }

    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      const res = await fetch(`${apiUrl}/api/interview/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_name: candidateName,
          config: {
            role: selectedRole,
            experience_level: selectedLevel,
            job_description: jobDescription || undefined,
            topics: selectedTopics,
            duration_minutes: durationMinutes,
            language: language
          }
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const session: InterviewSession = await res.json();
      onStartSession(session);
    } catch (err: any) {
      console.error('Failed to create session:', err);
      setErrorMsg(err.message || 'Failed to configure interview session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="interview-setup-container">
      {/* Top Header Bar */}
      <div className="setup-header">
        <div>
          <span className="badge badge-purple">Knowledge RAG Guided Interview • v0.11.0</span>
          <h2 className="setup-title">Configure Technical Interview</h2>
          <p className="setup-subtitle">
            Tailor the AI interviewer to specific engineering roles, seniority expectations, company standards, and target job descriptions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-secondary history-toggle-btn"
            onClick={() => setShowKnowledgeDrawer(!showKnowledgeDrawer)}
          >
            <span>📚 Knowledge Base</span>
            <span className="history-count">{knowledgeDocs.length}</span>
          </button>

          <button
            className="btn btn-secondary history-toggle-btn"
            onClick={() => setShowHistory(!showHistory)}
          >
            <span>📜 Past Sessions</span>
            {pastSessions.length > 0 && (
              <span className="history-count">{pastSessions.length}</span>
            )}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="error-banner" style={{ marginBottom: '20px' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Knowledge Base Drawer */}
      {showKnowledgeDrawer && (
        <div className="past-sessions-drawer">
          <div className="drawer-header">
            <div>
              <h4>📚 Company Engineering Standards & Rubrics</h4>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Indexed for mid-interview Retrieval-Augmented Generation (RAG)
              </span>
            </div>
            <button className="btn-close" onClick={() => setShowKnowledgeDrawer(false)}>✕</button>
          </div>

          <div className="knowledge-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            {knowledgeDocs.map((doc) => (
              <div key={doc.id} className="history-card">
                <div className="history-card-header">
                  <span className="history-role" style={{ fontSize: '13px' }}>{doc.title}</span>
                  <span className="history-status" style={{ fontSize: '9px' }}>{doc.category}</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4, margin: '6px 0' }}>
                  {doc.content.slice(0, 140)}...
                </p>
                <div className="history-topics">
                  {doc.tags.map((tag, i) => (
                    <span key={i} className="topic-tag-mini">{tag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Ingest Form */}
          <form onSubmit={handleIngestDoc} style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h5 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '10px' }}>+ Ingest Company Document / Rubric</h5>
            <div className="form-row">
              <input
                type="text"
                value={newDocTitle}
                onChange={(e) => setNewDocTitle(e.target.value)}
                placeholder="Standard Title (e.g. Distributed Lock Guidelines)"
                className="input-field flex-1"
                required
              />
              <input
                type="text"
                value={newDocTags}
                onChange={(e) => setNewDocTags(e.target.value)}
                placeholder="Comma tags (e.g. idempotency, redis, api)"
                className="input-field flex-1"
              />
              <select
                value={newDocCategory}
                onChange={(e) => setNewDocCategory(e.target.value)}
                className="input-field select-field"
              >
                <option value="company_standards">Company Standard</option>
                <option value="architecture_patterns">Architecture Pattern</option>
                <option value="question_bank">Question Bank</option>
                <option value="job_rubric">Job Rubric</option>
              </select>
            </div>
            <textarea
              value={newDocContent}
              onChange={(e) => setNewDocContent(e.target.value)}
              placeholder="Full text content of the engineering standard, failure guidelines, or rubric..."
              className="input-field textarea-field"
              style={{ minHeight: '60px', marginTop: '8px' }}
              required
            />
            <button type="submit" className="btn btn-secondary btn-sm" style={{ marginTop: '8px' }}>
              Index Document into RAG
            </button>
          </form>
        </div>
      )}

      {/* Past Sessions Drawer */}
      {showHistory && (
        <div className="past-sessions-drawer">
          <div className="drawer-header">
            <h4>Previous Interview Sessions</h4>
            <button className="btn-close" onClick={() => setShowHistory(false)}>✕</button>
          </div>
          {pastSessions.length === 0 ? (
            <p className="empty-history">No past interviews found in database.</p>
          ) : (
            <div className="history-grid">
              {pastSessions.map((sess) => (
                <div
                  key={sess.session_id}
                  className="history-card"
                  onClick={() => onStartSession(sess)}
                >
                  <div className="history-card-header">
                    <span className="history-role">{sess.config.role}</span>
                    <span className="history-status">{sess.status}</span>
                  </div>
                  <div className="history-meta">
                    <span>🧑 {sess.candidate_name}</span>
                    <span>⚡ {sess.turn_count} turns</span>
                    <span>⏱️ {sess.config.duration_minutes}m</span>
                  </div>
                  <div className="history-topics">
                    {sess.config.topics.slice(0, 3).map((t, idx) => (
                      <span key={idx} className="topic-tag-mini">{t}</span>
                    ))}
                  </div>
                  <span className="history-date">
                    {new Date(sess.created_at).toLocaleDateString()} • {new Date(sess.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="setup-grid">
        {/* Left Column: Role & Seniority */}
        <div className="setup-section">
          <div className="form-group">
            <label className="section-label">1. Candidate Information</label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="Candidate Full Name"
              className="input-field"
            />
          </div>

          <div className="form-group">
            <label className="section-label">2. Select Technical Role</label>
            <div className="roles-grid">
              {ROLES.map((role) => (
                <div
                  key={role.id}
                  className={`role-card ${selectedRole === role.id ? 'active' : ''}`}
                  onClick={() => setSelectedRole(role.id)}
                >
                  <div className="role-card-top">
                    <span className="role-icon">{role.icon}</span>
                    <span className="role-name">{role.title}</span>
                  </div>
                  <p className="role-desc">{role.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="section-label">3. Target Seniority Level</label>
            <div className="levels-grid">
              {EXPERIENCE_LEVELS.map((level) => (
                <div
                  key={level.id}
                  className={`level-card ${selectedLevel === level.id ? 'active' : ''}`}
                  onClick={() => setSelectedLevel(level.id)}
                >
                  <div className="level-label">{level.label}</div>
                  <div className="level-sub">{level.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Topics, Duration, JD */}
        <div className="setup-section">
          <div className="form-group">
            <label className="section-label">4. Session Duration & Language</label>
            <div className="form-row">
              <div className="flex-1">
                <select
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  className="input-field select-field"
                >
                  <option value={15}>15 Minutes (Screening)</option>
                  <option value={30}>30 Minutes (Standard)</option>
                  <option value={45}>45 Minutes (Full Deep Dive)</option>
                  <option value={60}>60 Minutes (Staff / Principal)</option>
                </select>
              </div>
              <div className="flex-1">
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="input-field select-field"
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi (हिंदी)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="section-label">5. Evaluation Focus Topics ({selectedTopics.length})</label>
            <div className="topics-cloud">
              {AVAILABLE_TOPICS.map((topic) => (
                <button
                  type="button"
                  key={topic}
                  className={`topic-chip ${selectedTopics.includes(topic) ? 'selected' : ''}`}
                  onClick={() => toggleTopic(topic)}
                >
                  <span>{selectedTopics.includes(topic) ? '✓' : '+'}</span>
                  <span>{topic}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="section-label">6. Custom Job Description (Optional)</label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste raw Job Description (JD) text, key requirements, or company tech stack here to ground the interviewer..."
              className="input-field textarea-field"
              rows={4}
            />
          </div>

          <button
            className="btn btn-primary btn-full btn-launch-interview"
            onClick={handleCreateAndLaunch}
            disabled={isSubmitting}
          >
            <span>{isSubmitting ? 'Configuring Session...' : '🚀 Launch Technical Interview'}</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};
