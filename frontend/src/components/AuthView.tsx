import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface AuthViewProps {
  apiUrl: string;
}

export const AuthView: React.FC<AuthViewProps> = ({ apiUrl }) => {
  const [isSignup, setIsSignup] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [fullName, setFullName] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    const endpoint = isSignup ? `${apiUrl}/api/auth/signup` : `${apiUrl}/api/auth/login`;
    const payload = isSignup
      ? { email, password, full_name: fullName }
      : { email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      login(data.token, {
        user_id: data.user_id,
        email: data.email,
        full_name: data.full_name
      });

      navigate('/dashboard');
    } catch (err: any) {
      console.error('Auth error:', err);
      setErrorMsg(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <button className="btn-back-link" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <div className="auth-header">
          <div className="badge">{isSignup ? 'Create Account' : 'Welcome Back'}</div>
          <h2 className="auth-title">
            {isSignup ? 'Register on VoiceHire' : 'Sign in to VoiceHire'}
          </h2>
          <p className="auth-subtitle">
            {isSignup
              ? 'Access candidate scorecards, evaluation reports, and interview histories.'
              : 'Log in with your email to view your assessment records and reports.'}
          </p>
        </div>

        {errorMsg && <div className="error-banner">{errorMsg}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {isSignup && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Chen"
                className="input-field"
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="candidate@example.com"
              className="input-field"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="input-field"
              required
              minLength={6}
            />
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={isSubmitting}>
            <span>{isSubmitting ? 'Processing...' : isSignup ? 'Create Account' : 'Sign In'}</span>
            <span>→</span>
          </button>
        </form>

        <div className="auth-footer">
          {isSignup ? (
            <p>
              Already have an account?{' '}
              <button type="button" className="auth-toggle-link" onClick={() => setIsSignup(false)}>
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don't have an account yet?{' '}
              <button type="button" className="auth-toggle-link" onClick={() => setIsSignup(true)}>
                Create an Account
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
