import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface ReportViewProps {
  apiUrl: string;
}

export const ReportView: React.FC<ReportViewProps> = ({ apiUrl }) => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<any>(null);
  const [scorecard, setScorecard] = useState<any>(null);
  const [evidenceReport, setEvidenceReport] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchFullReport = async () => {
      if (!sessionId) return;
      try {
        const [sessRes, scoreRes, evRes] = await Promise.all([
          fetch(`${apiUrl}/api/interview/session/${sessionId}`),
          fetch(`${apiUrl}/api/interview/session/${sessionId}/scorecard`),
          fetch(`${apiUrl}/api/interview/session/${sessionId}/evidence-report`)
        ]);

        if (!sessRes.ok) {
          throw new Error('Interview session not found');
        }

        const sessData = await sessRes.json();
        setSession(sessData);

        if (scoreRes.ok) {
          const scData = await scoreRes.json();
          setScorecard(scData);
        }

        if (evRes.ok) {
          const evData = await evRes.json();
          setEvidenceReport(evData);
        }
      } catch (err: any) {
        console.error('Report error:', err);
        setErrorMsg(err.message || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    };

    fetchFullReport();
  }, [apiUrl, sessionId]);

  if (loading) {
    return (
      <div className="report-container">
        <div className="loading-state">Generating assessment report...</div>
      </div>
    );
  }

  if (errorMsg || !session) {
    return (
      <div className="report-container">
        <button className="btn-back-link" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
        <div className="error-banner">{errorMsg || 'Session not found'}</div>
      </div>
    );
  }

  const score = scorecard?.overall_score || 0;
  const rec = evidenceReport?.recommendation || (score >= 3.5 ? 'HIRE' : score >= 2.5 ? 'BORDERLINE' : 'NO_HIRE');

  return (
    <div className="report-container">
      {/* Top Bar with Back Button */}
      <div className="report-header-nav">
        <button className="btn-back-link" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => window.print()}>
            Print / Export PDF
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/setup')}>
            New Assessment
          </button>
        </div>
      </div>

      {/* Candidate Executive Summary Header Card */}
      <div className="report-hero-card">
        <div className="report-hero-left">
          <span className="badge">Candidate Assessment Report</span>
          <h2 className="report-candidate-name">{session.candidate_name}</h2>
          <div className="report-meta-row">
            <span>Role: <strong>{session.config.role}</strong></span>
            <span>Seniority: <strong>{session.config.experience_level}</strong></span>
            <span>Duration: <strong>{session.config.duration_minutes}m</strong></span>
            <span>Date: <strong>{new Date(session.created_at).toLocaleDateString()}</strong></span>
          </div>
        </div>

        <div className="report-hero-right">
          <div className="hero-score-val">
            {score.toFixed(1)}
            <span style={{ fontSize: '16px', color: 'var(--text-muted)' }}> / 5.0</span>
          </div>
          <span className={`recommendation-badge ${rec.toLowerCase()}`}>
            {rec.replace('_', ' ')}
          </span>
          <div className="verdict-reason">
            {evidenceReport?.recommendation_reasoning || scorecard?.summary_verdict || 'Evaluation completed across technical competencies.'}
          </div>
        </div>
      </div>

      {/* 5-Dimensional Competency Breakdown */}
      <div className="report-section-card">
        <h3 className="section-title">Dimensional Competency Breakdown</h3>
        <div className="dimensions-breakdown">
          <div className="dim-row">
            <div className="dim-header">
              <span>1. Technical Correctness</span>
              <span className="dim-val">{scorecard?.avg_correctness?.toFixed(1) || '0.0'} / 5.0</span>
            </div>
            <div className="dim-bar-bg">
              <div className="dim-bar-fill" style={{ width: `${((scorecard?.avg_correctness || 0) / 5) * 100}%` }}></div>
            </div>
          </div>

          <div className="dim-row">
            <div className="dim-header">
              <span>2. Depth & Mechanics</span>
              <span className="dim-val">{scorecard?.avg_depth?.toFixed(1) || '0.0'} / 5.0</span>
            </div>
            <div className="dim-bar-bg">
              <div className="dim-bar-fill" style={{ width: `${((scorecard?.avg_depth || 0) / 5) * 100}%`, background: 'var(--accent-purple)' }}></div>
            </div>
          </div>

          <div className="dim-row">
            <div className="dim-header">
              <span>3. Trade-off Awareness</span>
              <span className="dim-val">{scorecard?.avg_tradeoffs?.toFixed(1) || '0.0'} / 5.0</span>
            </div>
            <div className="dim-bar-bg">
              <div className="dim-bar-fill" style={{ width: `${((scorecard?.avg_tradeoffs || 0) / 5) * 100}%`, background: 'var(--accent-green)' }}></div>
            </div>
          </div>

          <div className="dim-row">
            <div className="dim-header">
              <span>4. Practical Engineering vs Theory</span>
              <span className="dim-val">{scorecard?.avg_practical?.toFixed(1) || '0.0'} / 5.0</span>
            </div>
            <div className="dim-bar-bg">
              <div className="dim-bar-fill" style={{ width: `${((scorecard?.avg_practical || 0) / 5) * 100}%`, background: 'var(--accent-yellow)' }}></div>
            </div>
          </div>

          <div className="dim-row">
            <div className="dim-header">
              <span>5. Communication Clarity</span>
              <span className="dim-val">{scorecard?.avg_clarity?.toFixed(1) || '0.0'} / 5.0</span>
            </div>
            <div className="dim-bar-bg">
              <div className="dim-bar-fill" style={{ width: `${((scorecard?.avg_clarity || 0) / 5) * 100}%`, background: 'var(--accent-blue)' }}></div>
            </div>
          </div>
        </div>

        {/* Strengths & Development Areas */}
        <div className="scorecard-notes-grid" style={{ marginTop: '24px' }}>
          <div className="notes-box strengths">
            <h5>Key Strengths</h5>
            <ul>
              {scorecard?.top_strengths?.map((s: string, idx: number) => (
                <li key={idx}>{s}</li>
              )) || <li>No strengths recorded.</li>}
            </ul>
          </div>
          <div className="notes-box gaps">
            <h5>Development Areas</h5>
            <ul>
              {scorecard?.areas_for_improvement?.map((g: string, idx: number) => (
                <li key={idx}>{g}</li>
              )) || <li>No major gaps noted.</li>}
            </ul>
          </div>
        </div>
      </div>

      {/* Critical Red Flags Section (if any detected) */}
      {evidenceReport?.red_flags && evidenceReport.red_flags.length > 0 && (
        <div className="report-section-card red-flags-card">
          <h3 className="section-title" style={{ color: '#f87171' }}>
            Critical Technical Flags ({evidenceReport.red_flags.length})
          </h3>
          <div className="red-flags-grid">
            {evidenceReport.red_flags.map((rf: any, idx: number) => (
              <div key={idx} className="red-flag-card">
                <div className="red-flag-top">
                  <span className={`severity-badge ${rf.severity.toLowerCase()}`}>{rf.severity}</span>
                  <span className="flag-category">{rf.category}</span>
                </div>
                <div className="flag-quote">"{rf.quote}"</div>
                <div className="flag-explanation">{rf.explanation}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verbatim Transcript Quotations */}
      <div className="report-section-card">
        <h3 className="section-title">Verbatim Transcript Evidence</h3>
        <div className="evidence-quotes-grid">
          {evidenceReport?.key_strengths_with_evidence?.map((snip: any, idx: number) => (
            <div key={idx} className="quote-evidence-card strength">
              <div className="quote-header">
                <span className="quote-tag strength">STRENGTH • {snip.dimension}</span>
                <span className="quote-stage">{snip.stage}</span>
              </div>
              <div className="quote-body">"{snip.quote}"</div>
              <div className="quote-rationale">✓ {snip.rationale}</div>
            </div>
          ))}

          {evidenceReport?.key_weaknesses_with_evidence?.map((snip: any, idx: number) => (
            <div key={idx} className="quote-evidence-card gap">
              <div className="quote-header">
                <span className="quote-tag gap">GAP • {snip.dimension}</span>
                <span className="quote-stage">{snip.stage}</span>
              </div>
              <div className="quote-body">"{snip.quote}"</div>
              <div className="quote-rationale">⚠️ {snip.rationale}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Complete Raw Transcript Log */}
      {session.transcripts && session.transcripts.length > 0 && (
        <div className="report-section-card">
          <h3 className="section-title">Complete Dialogue Transcript ({session.transcripts.length} exchanges)</h3>
          <div className="report-transcripts-list">
            {session.transcripts.map((t: any, idx: number) => (
              <div key={idx} className={`transcript-log-item ${t.role}`}>
                <div className="log-header">
                  <strong>{t.role === 'interviewer' ? 'AI Interviewer' : session.candidate_name}</strong>
                  <span className="log-stage">{t.stage?.toUpperCase()}</span>
                </div>
                <div className="log-text">{t.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
