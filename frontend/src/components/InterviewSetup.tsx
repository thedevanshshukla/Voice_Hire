import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export interface InterviewConfig {
  role: string;
  experience_level: string;
  job_description?: string;
  resume_text?: string;
  topics?: string[];
  duration_minutes: number;
  language: string;
  user_email?: string;
}

export interface InterviewSession {
  session_id: string;
  candidate_id: string;
  candidate_name: string;
  user_email?: string;
  config: InterviewConfig;
  status: string;
  created_at: string;
  turn_count: number;
}

interface InterviewSetupProps {
  apiUrl: string;
  onStartSession?: (session: InterviewSession) => void;
}

const ROLES = [
  { id: 'Backend Engineer', title: 'Backend Engineer', desc: 'Databases, APIs, concurrency, and distributed services.' },
  { id: 'Frontend Engineer', title: 'Frontend Engineer', desc: 'React, performance, state architecture, and browser APIs.' },
  { id: 'Fullstack Engineer', title: 'Fullstack Engineer', desc: 'End-to-end web architectures, backend logic, and interfaces.' },
  { id: 'DevOps / SRE Engineer', title: 'DevOps / SRE', desc: 'CI/CD, Kubernetes, cloud infrastructure, and site reliability.' },
  { id: 'Distributed Systems Architect', title: 'Systems Architect', desc: 'High-availability, consensus, sharding, and resilience.' }
];

const EXPERIENCE_LEVELS = [
  { id: 'SDE-1 (0-2 years)', label: 'SDE-1', sub: '0-2 yrs • Core Fundamentals' },
  { id: 'SDE-2 (2-5 years)', label: 'SDE-2', sub: '2-5 yrs • Practical System Depth' },
  { id: 'Senior / SDE-3 (5-8 years)', label: 'Senior', sub: '5-8 yrs • Scale & Tradeoffs' },
  { id: 'Staff / Principal (8+ years)', label: 'Staff+', sub: '8+ yrs • Architecture & Strategy' }
];

export const InterviewSetup: React.FC<InterviewSetupProps> = ({ apiUrl, onStartSession }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [candidateName, setCandidateName] = useState(user?.full_name || 'Alex Chen');
  const [selectedRole, setSelectedRole] = useState('Backend Engineer');
  const [selectedLevel, setSelectedLevel] = useState('SDE-2 (2-5 years)');
  
  // Resume & Job Description
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [resumeText, setResumeText] = useState<string>('');
  const [showResumeEditor, setShowResumeEditor] = useState<boolean>(false);
  const [jobDescription, setJobDescription] = useState<string>('');

  const [durationMinutes, setDurationMinutes] = useState(30);
  const [language, setLanguage] = useState('English');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (user?.full_name) {
      setCandidateName(user.full_name);
    }
  }, [user]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setResumeFileName(file.name);

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setResumeText(content);
      }
    };

    // Read plain text / markdown / code files directly
    reader.readAsText(file);
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
          user_email: user?.email || undefined,
          config: {
            role: selectedRole,
            experience_level: selectedLevel,
            job_description: jobDescription.trim() || undefined,
            resume_text: resumeText.trim() || undefined,
            topics: ['Architecture & Design', 'Databases & Storage', 'APIs & Concurrency', 'Resume Deep Dive'],
            duration_minutes: durationMinutes,
            language: language,
            user_email: user?.email || undefined
          }
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const session: InterviewSession = await res.json();
      if (onStartSession) {
        onStartSession(session);
      }
      navigate(`/interview/${session.session_id}`);
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
          <button className="btn-back-link" onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </button>
          <span className="badge badge-purple">Candidate Assessment Setup</span>
          <h2 className="setup-title">Interview Configuration</h2>
          <p className="setup-subtitle">
            Upload your resume so the AI interviewer can deeply examine your real-world projects, architecture decisions, and role alignment.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="error-banner" style={{ marginBottom: '20px' }}>
          {errorMsg}
        </div>
      )}

      <div className="setup-grid">
        {/* Left Column: Role & Seniority */}
        <div className="setup-section">
          <div className="form-group">
            <label className="section-label">Candidate Name</label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="Candidate Full Name"
              className="input-field"
            />
          </div>

          <div className="form-group">
            <label className="section-label">Target Role</label>
            <div className="roles-grid">
              {ROLES.map((role) => (
                <div
                  key={role.id}
                  className={`role-card ${selectedRole === role.id ? 'active' : ''}`}
                  onClick={() => setSelectedRole(role.id)}
                >
                  <div className="role-card-top">
                    <span className="role-name">{role.title}</span>
                  </div>
                  <p className="role-desc">{role.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="section-label">Seniority Tier</label>
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

        {/* Right Column: Resume Upload, JD, Duration */}
        <div className="setup-section">
          {/* Resume Upload Box */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label className="section-label" style={{ margin: 0 }}>
                Candidate Resume / Work History
              </label>
              {resumeText && (
                <button
                  type="button"
                  className="auth-toggle-link"
                  style={{ fontSize: '12px' }}
                  onClick={() => setShowResumeEditor(!showResumeEditor)}
                >
                  {showResumeEditor ? 'Hide Text' : 'View / Edit Resume Text'}
                </button>
              )}
            </div>

            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.txt,.doc,.docx,.md"
              onChange={handleFileUpload}
            />

            <div
              className={`resume-upload-dropzone ${resumeText ? 'has-file' : ''}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="upload-icon">📄</div>
              {resumeFileName ? (
                <div>
                  <div className="upload-title">✓ {resumeFileName}</div>
                  <div className="upload-sub">
                    {resumeText.length > 0
                      ? `${resumeText.length} characters loaded • Click to replace file`
                      : 'File selected • Click to change'}
                  </div>
                </div>
              ) : (
                <div>
                  <div className="upload-title">Upload Candidate Resume (.pdf, .txt, .docx)</div>
                  <div className="upload-sub">
                    Click to browse or upload your project summary
                  </div>
                </div>
              )}
            </div>

            {/* Optional Direct Paste / Editor */}
            {(!resumeText || showResumeEditor) && (
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Or paste your resume text, key projects, tech stack, and achievements directly here..."
                className="input-field textarea-field"
                rows={4}
                style={{ marginTop: '8px', fontSize: '12px' }}
              />
            )}
          </div>

          {/* Target Job Description */}
          <div className="form-group">
            <label className="section-label">Target Job Description & Stack (Optional)</label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the target job description or required company tech stack here (e.g. Distributed Kafka, Go microservices, PostgreSQL)..."
              className="input-field textarea-field"
              rows={3}
            />
          </div>

          {/* Duration & Language */}
          <div className="form-group">
            <label className="section-label">Duration & Language</label>
            <div className="form-row">
              <div className="flex-1">
                <select
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  className="input-field select-field"
                >
                  <option value={15}>15 Minutes (Screening)</option>
                  <option value={30}>30 Minutes (Standard)</option>
                  <option value={45}>45 Minutes (Deep Dive)</option>
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
                  <option value="Hinglish">Hinglish (Conversational Technical)</option>
                  <option value="Hindi">Hindi (हिंदी)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary btn-full btn-launch-interview"
            onClick={handleCreateAndLaunch}
            disabled={isSubmitting}
            style={{ marginTop: '12px' }}
          >
            <span>{isSubmitting ? 'Preparing AI Interviewer...' : 'Begin Technical Assessment'}</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};
