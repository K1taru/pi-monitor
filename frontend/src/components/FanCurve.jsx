import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Minus, Save, AlertCircle, Check } from 'lucide-react';
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
        setPoints(res.data.points);
      }
    } catch (err) {
      console.error('Error fetching fan curve:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = (index, speed) => {
    const sorted = getSorted();
    const realIndex = sortedToReal(index);
    const updated = [...points];
    updated[realIndex] = {
      ...updated[realIndex],
      speed: Math.max(0, Math.min(100, Number(speed))),
    };
    setPoints(updated);
  };

  const handleTempChange = (index, temp) => {
    const realIndex = sortedToReal(index);
    const updated = [...points];
    updated[realIndex] = {
      ...updated[realIndex],
      temp: Math.max(0, Math.min(110, Number(temp))),
    };
    setPoints(updated);
  };

  const getSorted = () =>
    [...points]
      .map((p, i) => ({ ...p, _i: i }))
      .sort((a, b) => a.temp - b.temp);

  const sortedToReal = (sortedIdx) => getSorted()[sortedIdx]._i;

  const addPoint = () => {
    if (points.length >= 10) return;
    const sorted = getSorted();
    const last = sorted[sorted.length - 1];
    setPoints([
      ...points,
      {
        temp: Math.min(110, (last?.temp || 50) + 10),
        speed: Math.min(100, (last?.speed || 50) + 10),
      },
    ]);
  };

  const removePoint = (sortedIdx) => {
    if (points.length <= 1) return;
    const realIndex = sortedToReal(sortedIdx);
    setPoints(points.filter((_, i) => i !== realIndex));
  };

  const saveCurve = async () => {
    try {
      const sorted = [...points].sort((a, b) => a.temp - b.temp);
      await axios.post('/system/fan/curve', { points: sorted });
      setPoints(sorted);
      showMessage('success', 'Fan curve saved');
    } catch (err) {
      showMessage(
        'error',
        err.response?.data?.error || 'Failed to save curve'
      );
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  if (loading) return null;

  const sorted = getSorted();

  return (
    <div className="fan-curve-container">
      {message && (
        <div className={`curve-message ${message.type}`}>
          {message.type === 'success' ? (
            <Check size={16} />
          ) : (
            <AlertCircle size={16} />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="mixer-board">
        {sorted.map((point, index) => (
          <div className="channel-strip" key={index}>
            {/* Speed display */}
            <div className="channel-display">
              <span className="speed-value">{point.speed}%</span>
            </div>

            {/* Vertical fader */}
            <div className="fader-track">
              <div
                className="fader-fill"
                style={{ height: `${point.speed}%` }}
              />
              <input
                type="range"
                min="0"
                max="100"
                value={point.speed}
                onChange={(e) => handleSpeedChange(index, e.target.value)}
                className="fader-input"
              />
            </div>

            {/* LED meter */}
            <div className="led-meter">
              {[...Array(8)].map((_, i) => {
                const threshold = ((7 - i) / 7) * 100;
                const active = point.speed >= threshold;
                const color =
                  i < 2 ? 'led-red' : i < 4 ? 'led-yellow' : 'led-green';
                return (
                  <div
                    key={i}
                    className={`led ${color} ${active ? 'active' : ''}`}
                  />
                );
              })}
            </div>

            {/* Temperature input */}
            <div className="channel-label">
              <input
                type="number"
                min="0"
                max="110"
                value={point.temp}
                onChange={(e) => handleTempChange(index, e.target.value)}
                className="temp-input"
              />
              <span className="temp-unit">°C</span>
            </div>

            {/* Remove button */}
            {points.length > 1 && (
              <button
                className="channel-remove"
                onClick={() => removePoint(index)}
                title="Remove point"
              >
                <Minus size={12} />
              </button>
            )}
          </div>
        ))}

        {/* Add channel */}
        {points.length < 10 && (
          <button className="add-channel" onClick={addPoint}>
            <Plus size={20} />
            <span>Add</span>
          </button>
        )}
      </div>

      <div className="curve-actions">
        <span className="curve-hint">
          {points.length}/10 points — drag faders to set fan speed per temperature
        </span>
        <button className="btn btn-primary" onClick={saveCurve}>
          <Save size={16} />
          Save Curve
        </button>
      </div>
    </div>
  );
}

export default FanCurve;
