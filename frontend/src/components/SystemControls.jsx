import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, Cpu, Fan, Power, AlertCircle, Check } from 'lucide-react';
import './SystemControls.css';

function SystemControls() {
  const [governor, setGovernor] = useState({
    current: '',
    available: []
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchGovernor();
  }, []);

  const fetchGovernor = async () => {
    try {
      const response = await axios.get('/api/system/governor');
      setGovernor(response.data);
    } catch (error) {
      console.error('Error fetching governor:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGovernorChange = async (newGovernor) => {
    try {
      await axios.post('/api/system/governor', { governor: newGovernor });
      showMessage('success', `CPU governor changed to ${newGovernor}`);
      await fetchGovernor();
    } catch (error) {
      showMessage('error', error.response?.data?.error || 'Failed to change governor');
    }
  };

  const handleReboot = async () => {
    if (!confirm('Are you sure you want to reboot the system? This will disconnect all users.')) {
      return;
    }

    try {
      await axios.post('/api/system/reboot');
      showMessage('success', 'System is rebooting...');
    } catch (error) {
      showMessage('error', error.response?.data?.error || 'Failed to reboot system');
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const governorDescriptions = {
    'ondemand': 'Dynamically scales frequency based on load',
    'performance': 'Always runs at maximum frequency',
    'powersave': 'Always runs at minimum frequency',
    'conservative': 'Similar to ondemand but more gradual',
    'schedutil': 'Scheduler-driven CPU frequency selection'
  };

  if (loading) {
    return (
      <div className="card">
        <div className="loading-spinner"></div>
        <p className="text-center">Loading system controls...</p>
      </div>
    );
  }

  return (
    <div className="system-controls-container">
      {message && (
        <div className={`message-banner ${message.type}`}>
          {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* CPU Governor Control */}
      <div className="card control-section">
        <div className="section-icon">
          <Cpu size={32} />
        </div>
        
        <h2>CPU Performance Profile</h2>
        <p className="section-description">
          Control how the CPU manages its frequency and power consumption
        </p>

        <div className="current-setting">
          <span className="label">Current Governor:</span>
          <span className="value">{governor.current || 'Unknown'}</span>
        </div>

        <div className="governor-grid">
          {governor.available.map((gov) => (
            <button
              key={gov}
              className={`governor-card ${governor.current === gov ? 'active' : ''}`}
              onClick={() => handleGovernorChange(gov)}
              disabled={governor.current === gov}
            >
              <div className="governor-name">{gov}</div>
              <div className="governor-description">
                {governorDescriptions[gov] || 'CPU frequency governor'}
              </div>
              {governor.current === gov && (
                <div className="active-badge">
                  <Check size={16} />
                  Active
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Fan Control (Placeholder) */}
      <div className="card control-section">
        <div className="section-icon">
          <Fan size={32} />
        </div>
        
        <h2>Fan Control</h2>
        <p className="section-description">
          Adjust cooling fan speed settings
        </p>

        <div className="info-box">
          <AlertCircle size={20} />
          <div>
                <p><strong>Fan control not configured</strong></p>
            <p className="text-muted">
              To enable fan control, install a fan control daemon and configure the backend API.
            </p>
          </div>
        </div>
      </div>

      {/* System Power */}
      <div className="card control-section danger-zone">
        <div className="section-icon danger">
          <Power size={32} />
        </div>
        
        <h2>System Power</h2>
        <p className="section-description">
          Manage system power state
        </p>

        <div className="danger-warning">
          <AlertCircle size={20} />
          <span>Warning: These actions will affect system availability</span>
        </div>

        <div className="power-controls">
          <button 
            className="btn btn-danger"
            onClick={handleReboot}
          >
            <Power size={18} />
            Reboot System
          </button>
        </div>
      </div>

      {/* Additional Info */}
      <div className="card info-section">
        <h3>System Control Information</h3>
        <ul className="info-list">
          <li>
            <strong>Performance Mode:</strong> Maximum CPU frequency, higher power consumption, 
            best for intensive tasks
          </li>
          <li>
            <strong>Ondemand Mode:</strong> Balanced performance and power efficiency, 
            scales based on load
          </li>
          <li>
            <strong>Powersave Mode:</strong> Minimum CPU frequency, lowest power consumption, 
            suitable for idle systems
          </li>
          <li>
            <strong>Root Access:</strong> Some controls require sudo privileges. Ensure the 
            backend has proper permissions.
          </li>
        </ul>
      </div>
    </div>
  );
}

export default SystemControls;
