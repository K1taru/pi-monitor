import React, { useState } from 'react';
import axios from 'axios';
import { Terminal, Lock, AlertCircle } from 'lucide-react';
import '../styles/Login.css';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password,
      });

      onLogin(response.data.access_token, {
        username: response.data.username,
        is_admin: response.data.is_admin,
      });
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-background">
        <div className="login-grid"></div>
      </div>
      
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-icon">
              <Terminal size={48} />
            </div>
            <h1>RASPY MONITOR</h1>
            <p className="login-subtitle">System Access Control</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {error && (
              <div className="error-message">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="input-group">
              <label htmlFor="username">
                <Lock size={14} />
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                autoComplete="username"
              />
            </div>

            <div className="input-group">
              <label htmlFor="password">
                <Lock size={14} />
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Authenticating...' : 'Access System'}
            </button>
          </form>

          <div className="login-footer">
            <p className="text-muted">Change password after first login</p>
          </div>
        </div>

        <div className="login-info">
          <div className="info-card">
            <h3>Secure Access</h3>
            <p>JWT-based authentication with encrypted sessions</p>
          </div>
          <div className="info-card">
            <h3>Real-time Monitoring</h3>
            <p>Live system metrics and performance tracking</p>
          </div>
          <div className="info-card">
            <h3>Remote Control</h3>
            <p>Manage your Raspberry Pi from anywhere</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
