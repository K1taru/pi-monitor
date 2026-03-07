import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, Cpu, Fan, Power, AlertCircle, Check, Wind, Zap } from 'lucide-react';
import FanCurve from './FanCurve';
import '../styles/SystemControls.css';

function SystemControls() {
  const [governor, setGovernor] = useState({
    current: '',
    available: []
  });
  const [fan, setFan] = useState({ available: false, speed: 50, rpm: 0, mode: 'auto' });
  const [fanSpeed, setFanSpeed] = useState(50);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    Promise.all([fetchGovernor(), fetchFan()]);
  }, []);

  const fetchGovernor = async () => {
    try {
      const response = await axios.get('/system/governor');
      setGovernor(response.data);
    } catch (error) {
      console.error('Error fetching governor:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFan = async () => {
    try {
      const response = await axios.get('/system/fan');
      setFan(response.data);
      if (response.data.speed !== undefined) setFanSpeed(response.data.speed);
    } catch (error) {
      console.error('Error fetching fan status:', error);
    }
  };

  const handleGovernorChange = async (newGovernor) => {
    try {
      await axios.post('/system/governor', { governor: newGovernor });
      showMessage('success', `CPU governor changed to ${newGovernor}`);
      await fetchGovernor();
    } catch (error) {
      showMessage('error', error.response?.data?.error || 'Failed to change governor');
    }
  };

  const handleFanMode = async (mode) => {
    try {
      const payload = { mode };
      if (mode === 'manual') payload.speed = fanSpeed;
      await axios.post('/system/fan', payload);
      const labels = { auto: 'Auto (curve)', manual: 'Manual', turbo: 'Turbo' };
      showMessage('success', `Fan mode: ${labels[mode]}`);
      await fetchFan();
    } catch (error) {
      showMessage('error', error.response?.data?.error || 'Failed to change fan mode');
    }
  };

  const handleFanSpeedApply = async () => {
    try {
      await axios.post('/system/fan', { mode: 'manual', speed: fanSpeed });
      showMessage('success', `Fan speed set to ${fanSpeed}%`);
      await fetchFan();
    } catch (error) {
      showMessage('error', error.response?.data?.error || 'Failed to set fan speed');
    }
  };

  const handleReboot = async () => {
    if (!confirm('Are you sure you want to reboot the system? This will disconnect all users.')) {
      return;
    }

    try {
      await axios.post('/system/reboot');
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

      {/* Fan Control */}
      <div className="card control-section">
        <div className="section-icon">
          <Fan size={32} />
        </div>

        <h2>Fan Control</h2>
        <p className="section-description">
          Adjust cooling fan speed or let the system manage it automatically
        </p>

        {!fan.available ? (
          <div className="info-box">
            <AlertCircle size={20} />
            <div>
              <p><strong>Fan PWM not detected</strong></p>
              <p className="text-muted">
                No hwmon device with PWM control was found. Ensure the fan is connected to the Pi&apos;s fan header.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="fan-status-row">
              <div className="fan-stat">
                <span className="label">RPM</span>
                <span className="value">
                  <Wind size={16} />
                  {fan.rpm > 0 ? fan.rpm : '—'}
                </span>
              </div>
              <div className="fan-stat">
                <span className="label">Speed</span>
                <span className="value">{fan.speed}%</span>
              </div>
              <div className="fan-stat">
                <span className="label">Mode</span>
                <span className={`value ${fan.mode === 'turbo' ? 'text-danger' : fan.mode === 'auto' ? 'text-accent' : ''}`}>
                  {fan.mode?.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Mode buttons */}
            <div className="fan-mode-buttons">
              <button
                className={`mode-btn ${fan.mode === 'auto' ? 'active auto' : ''}`}
                onClick={() => handleFanMode('auto')}
              >
                <Fan size={16} />
                Auto
              </button>
              <button
                className={`mode-btn ${fan.mode === 'manual' ? 'active manual' : ''}`}
                onClick={() => handleFanMode('manual')}
              >
                <Settings size={16} />
                Manual
              </button>
              <button
                className={`mode-btn turbo-btn ${fan.mode === 'turbo' ? 'active turbo' : ''}`}
                onClick={() => handleFanMode('turbo')}
              >
                <Zap size={16} />
                Turbo
              </button>
            </div>

            {/* Manual speed slider — only when in manual mode */}
            <div className={`fan-slider-group ${fan.mode !== 'manual' ? 'disabled' : ''}`}>
              <div className="slider-labels">
                <span>0%</span>
                <span className="slider-current">{fanSpeed}%</span>
                <span>100%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={fanSpeed}
                disabled={fan.mode !== 'manual'}
                onChange={(e) => setFanSpeed(Number(e.target.value))}
                className="fan-slider"
              />
              <button
                className="btn btn-secondary"
                onClick={handleFanSpeedApply}
                disabled={fan.mode !== 'manual'}
              >
                Apply Speed
              </button>
            </div>
          </>
        )}
      </div>

      {/* Fan Speed Curve */}
      {fan.available && (
        <div className="card control-section">
          <div className="section-icon">
            <Settings size={32} />
          </div>

          <h2>Fan Speed Curve</h2>
          <p className="section-description">
            Set temperature → fan speed mapping. Active when fan is in Auto mode.
          </p>

          <FanCurve />
        </div>
      )}

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
    </div>
  );
}

export default SystemControls;
