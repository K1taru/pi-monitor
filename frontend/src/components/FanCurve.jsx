import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, Save, AlertCircle, Check } from 'lucide-react';
import '../styles/FanCurve.css';

function FanCurve() {
  const [points, setPoints] = useState([]);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurve();
  }, []);

  const fetchCurve = async () => {
    try {
      const res = await axios.get('/system/fan/curve');
      if (res.data.points?.length) {
        setPoints(res.data.points.sort((a, b) => a.temp - b.temp));
      }
    } catch (err) {
      console.error('Error fetching fan curve:', err);
    } finally {
      setLoading(false);
    }
  };

  const updatePoint = (index, field, value) => {
    const max = field === 'temp' ? 110 : 100;
    const clamped = Math.max(0, Math.min(max, Number(value) || 0));
    const updated = points.map((p, i) =>
      i === index ? { ...p, [field]: clamped } : p
    );
    setPoints(updated.sort((a, b) => a.temp - b.temp));
  };

  const addPoint = () => {
    if (points.length >= 10) return;
    const last = points[points.length - 1];
    const newPoint = {
      temp: Math.min(110, (last?.temp || 50) + 10),
      speed: Math.min(100, (last?.speed || 50) + 10),
    };
    setPoints([...points, newPoint].sort((a, b) => a.temp - b.temp));
  };

  const removePoint = (index) => {
    if (points.length <= 1) return;
    setPoints(points.filter((_, i) => i !== index));
  };

  const saveCurve = async () => {
    try {
      await axios.post('/system/fan/curve', { points });
      showMessage('success', 'Fan curve saved');
    } catch (err) {
      showMessage('error', err.response?.data?.error || 'Failed to save curve');
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  if (loading) return null;

  return (
    <div className="fan-curve-container">
      {message && (
        <div className={`curve-message ${message.type}`}>
          {message.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="curve-table">
        <div className="curve-header">
          <span className="curve-col-temp">Temp</span>
          <span className="curve-col-speed">Speed</span>
          <span className="curve-col-bar"></span>
          <span className="curve-col-action"></span>
        </div>

        {points.map((point, index) => (
          <div className="curve-row" key={index}>
            <div className="curve-col-temp">
              <input
                type="range"
                min="0"
                max="110"
                value={point.temp}
                onChange={(e) => updatePoint(index, 'temp', e.target.value)}
                className="temp-slider"
              />
              <span className="temp-label">{point.temp}°C</span>
            </div>
            <div className="curve-col-speed">
              <input
                type="range"
                min="0"
                max="100"
                value={point.speed}
                onChange={(e) => updatePoint(index, 'speed', e.target.value)}
                className="speed-slider"
              />
              <span className="speed-label">{point.speed}%</span>
            </div>
            <div className="curve-col-bar">
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${point.speed}%` }}
                />
              </div>
            </div>
            <div className="curve-col-action">
              {points.length > 1 && (
                <button
                  className="remove-btn"
                  onClick={() => removePoint(index)}
                  title="Remove point"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="curve-actions">
        <div className="curve-actions-left">
          {points.length < 10 && (
            <button className="btn btn-ghost" onClick={addPoint}>
              <Plus size={16} />
              Add Point
            </button>
          )}
          <span className="curve-hint">{points.length}/10 points</span>
        </div>
        <button className="btn btn-primary" onClick={saveCurve}>
          <Save size={16} />
          Save Curve
        </button>
      </div>
    </div>
  );
}

export default FanCurve;
