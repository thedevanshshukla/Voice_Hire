import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface InterviewSessionSummary {
  session_id: string;
  candidate_name: string;
  user_email?: string;
  status: string;
  turn_count: number;
  created_at: string;
  config: {
    role: string;
    experience_level: string;
    duration_minutes: number;
    topics: string[];
    language: string;
  };
  scorecard?: {
    overall_score: number;
    summary_verdict: string;
    passed_recommendation: boolean;
    total_evaluated_turns: number;
    avg_correctness: number;
    avg_depth: number;
  };
  evidence_report?: {
    recommendation: string;
    confidence_score: number;
    red_flags: any[];
  };
}

interface DashboardViewProps {
  apiUrl: string;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ apiUrl }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<InterviewSessionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserSessions = async () => {
      try {
        const queryParam = user?.email ? `?user_email=${encodeURIComponent(user.email)}` : '';
        const res = await fetch(`${apiUrl}/api/interview/sessions${queryParam}`);
        if (res.ok) {
          const data = await res.json();
          setSessions(data);
        } else {
          setErrorMsg('Failed to retrieve assessment history');
        }
      } catch (err: any) {
        console.error('Dashboard fetch error:', err);
        setErrorMsg('Network error connecting to assessment database');
      } finally {
        setLoading(false);
      }
    };

    fetchUserSessions();
  }, [apiUrl, user]);

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <div className="dashboard-header">
        <div>
          <button className="btn-back-link" onClick={() => navigate('/')}>
            ← Back to Home
          </button>
          <h2 className="dashboard-title">Assessment Dashboard</h2>
          <p className="dashboard-subtitle">
            {user ? `Logged in as ${user.full_name} (${user.email})` : 'All Technical Assessments'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button className="btn btn-primary" onClick={() => navigate('/setup')}>
            <span>Configure New Interview</span>
            <span>+</span>
          </button>
          {user && (
            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Sign Out
            </button>
          )}
        </div>
      </div>

      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      {/* Metrics Summary Row */}
      <div className="dashboard-stats-grid">
        <div className="dash-stat-card">
          <div className="dash-stat-num">{sessions.length}</div>
          <div className="dash-stat-lbl">Total Interviews Conducted</div>
        </div>
        <div className="dash-stat-card">
          <div className="dash-stat-num">
            {sessions.filter((s) => s.evidence_report?.recommendation === 'STRONG_HIRE' || s.evidence_report?.recommendation === 'HIRE').length}
          </div>
          <div className="dash-stat-lbl">Pass / Hire Recommendations</div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="dashboard-sessions-section">
        <h3 className="section-heading">Candidate Evaluation Reports</h3>

        {loading ? (
          <div className="loading-state">Loading candidate records...</div>
        ) : sessions.length === 0 ? (
          <div className="empty-dashboard-card">
            <h4>No Assessment Sessions Found</h4>
            <p>You haven't conducted any technical interviews yet under this account.</p>
            <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => navigate('/setup')}>
              Launch Your First Interview
            </button>
          </div>
        ) : (
          <div className="reports-table-container">
            <table className="reports-table">
              <thead>
                <tr>
                  <th>Candidate & Date</th>
                  <th>Role & Seniority</th>
                  <th>Duration / Turns</th>
                  <th>Score</th>
                  <th>Recommendation</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((sess) => {
                  const score = sess.scorecard?.overall_score || 0;
                  const rec = sess.evidence_report?.recommendation || (score >= 3.5 ? 'HIRE' : score >= 2.5 ? 'BORDERLINE' : 'NO_HIRE');
                  return (
                    <tr key={sess.session_id} className="report-row" onClick={() => navigate(`/report/${sess.session_id}`)}>
                      <td>
                        <div className="cand-name">{sess.candidate_name}</div>
                        <div className="cand-date">
                          {new Date(sess.created_at).toLocaleDateString()} • {new Date(sess.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </td>
                      <td>
                        <div className="cand-role">{sess.config.role}</div>
                        <div className="cand-level">{sess.config.experience_level}</div>
                      </td>
                      <td>
                        <div>{sess.config.duration_minutes} mins</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{sess.turn_count} speech turns</div>
                      </td>
                      <td>
                        <span className="table-score-badge">
                          {score.toFixed(1)} / 5.0
                        </span>
                      </td>
                      <td>
                        <span className={`recommendation-badge ${rec.toLowerCase()}`}>
                          {rec.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/report/${sess.session_id}`);
                          }}
                        >
                          View Report →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
