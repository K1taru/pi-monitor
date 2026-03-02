import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import '../styles/SystemChart.css';

function SystemChart({ history, onTimeRangeChange }) {
  const [timeRange, setTimeRange] = useState(1);
  const [selectedMetrics, setSelectedMetrics] = useState({
    cpu_temp: true,
    cpu_percent: true,
    ram_percent: false,
    disk_percent: false,
  });

  const handleTimeRangeChange = (hours) => {
    setTimeRange(hours);
    if (onTimeRangeChange) onTimeRangeChange(hours);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const toggleMetric = (metric) => {
    setSelectedMetrics(prev => ({
      ...prev,
      [metric]: !prev[metric]
    }));
  };

  const metricsConfig = {
    cpu_temp: { name: 'CPU Temp (°C)', color: '#ff3366', yAxis: 'left' },
    cpu_percent: { name: 'CPU Usage (%)', color: '#00ff88', yAxis: 'right' },
    ram_percent: { name: 'RAM Usage (%)', color: '#00d4ff', yAxis: 'right' },
    disk_percent: { name: 'Disk Usage (%)', color: '#ffaa00', yAxis: 'right' },
  };

  // Format data for chart
  const chartData = history.map(point => ({
    time: formatTime(point.timestamp),
    cpu_temp: point.cpu_temp,
    cpu_percent: point.cpu_percent,
    ram_percent: point.ram_percent,
    disk_percent: point.disk_percent,
  }));

  return (
    <div className="system-chart-container">
      <div className="card">
        <div className="chart-header">
          <h2>System Performance History</h2>
          
          <div className="chart-controls">
            <div className="time-range-selector">
              <button
                className={timeRange === 1 ? 'active' : ''}
                onClick={() => handleTimeRangeChange(1)}
              >
                1H
              </button>
              <button
                className={timeRange === 6 ? 'active' : ''}
                onClick={() => handleTimeRangeChange(6)}
              >
                6H
              </button>
              <button
                className={timeRange === 24 ? 'active' : ''}
                onClick={() => handleTimeRangeChange(24)}
              >
                24H
              </button>
            </div>
          </div>
        </div>

        <div className="metric-toggles">
          {Object.entries(metricsConfig).map(([key, config]) => (
            <button
              key={key}
              className={`metric-toggle ${selectedMetrics[key] ? 'active' : ''}`}
              onClick={() => toggleMetric(key)}
              style={{
                borderColor: selectedMetrics[key] ? config.color : 'var(--border)',
              }}
            >
              <span 
                className="metric-indicator"
                style={{ backgroundColor: config.color }}
              ></span>
              {config.name}
            </button>
          ))}
        </div>

        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis 
                dataKey="time" 
                stroke="var(--text-secondary)"
                style={{ fontSize: '0.75rem' }}
              />
              <YAxis 
                yAxisId="left"
                stroke="var(--text-secondary)"
                style={{ fontSize: '0.75rem' }}
                label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                stroke="var(--text-secondary)"
                style={{ fontSize: '0.75rem' }}
                label={{ value: 'Usage (%)', angle: 90, position: 'insideRight' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                }}
                labelStyle={{ color: 'var(--text-primary)' }}
              />
              <Legend 
                wrapperStyle={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                }}
              />
              
              {selectedMetrics.cpu_temp && (
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="cpu_temp"
                  stroke={metricsConfig.cpu_temp.color}
                  name={metricsConfig.cpu_temp.name}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
              
              {selectedMetrics.cpu_percent && (
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cpu_percent"
                  stroke={metricsConfig.cpu_percent.color}
                  name={metricsConfig.cpu_percent.name}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
              
              {selectedMetrics.ram_percent && (
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="ram_percent"
                  stroke={metricsConfig.ram_percent.color}
                  name={metricsConfig.ram_percent.name}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
              
              {selectedMetrics.disk_percent && (
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="disk_percent"
                  stroke={metricsConfig.disk_percent.color}
                  name={metricsConfig.disk_percent.name}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {chartData.length === 0 && (
          <div className="no-data">
            <p>Collecting data... Check back in a minute.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SystemChart;
