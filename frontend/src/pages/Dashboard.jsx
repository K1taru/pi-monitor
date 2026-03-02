import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Cpu,
  MemoryStick,
  HardDrive,
  Thermometer,
  Gauge,
  Network,
  LogOut,
  Settings,
  Terminal as TerminalIcon,
  Clock,
  Activity,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import SystemChart from '../components/SystemChart';
import ProcessList from '../components/ProcessList';
import Terminal from '../components/Terminal';
import SystemControls from '../components/SystemControls';
import './Dashboard.css';

function Dashboard({ user, onLogout }) {
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({
    cpu: true,
    memory: true,
    disk: true,
  });

  // Fetch current metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await axios.get('/api/metrics/current');
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  }, []);

  // Fetch historical data
  const fetchHistory = useCallback(async (hours = 1) => {
    try {
      const response = await axios.get(`/api/metrics/history?hours=${hours}`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([fetchMetrics(), fetchHistory()]);
      setLoading(false);
    };

    loadData();

    // Refresh metrics every 2 seconds
    const metricsInterval = setInterval(fetchMetrics, 2000);
    
    // Refresh history every 30 seconds
    const historyInterval = setInterval(() => fetchHistory(), 30000);

    return () => {
      clearInterval(metricsInterval);
      clearInterval(historyInterval);
    };
  }, [fetchMetrics, fetchHistory]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatBytes = (bytes) => {
    const gb = bytes / (1024 ** 3);
    return gb.toFixed(2);
  };

  const getStatusColor = (percent) => {
    if (percent >= 90) return 'danger';
    if (percent >= 70) return 'warning';
    return 'normal';
  };

  const getTempStatus = (temp) => {
    if (temp >= 80) return 'danger';
    if (temp >= 70) return 'warning';
    return 'normal';
  };

  if (loading || !metrics) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Initializing System Monitor...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>RASPY MONITOR</h1>
          <div className="status-badge">
            <span className="status-dot online"></span>
            <span>SYSTEM ONLINE</span>
          </div>
        </div>

        <div className="header-right">
          <div className="user-info">
            <span className="user-name">{user.username}</span>
            {user.is_admin && <span className="admin-badge">ADMIN</span>}
          </div>
          <button className="btn btn-secondary" onClick={onLogout}>
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      {/* Navigation */}
      <nav className="dashboard-nav">
        <button
          className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity size={18} />
          Overview
        </button>
        <button
          className={`nav-item ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          <Gauge size={18} />
          Charts
        </button>
        <button
          className={`nav-item ${activeTab === 'processes' ? 'active' : ''}`}
          onClick={() => setActiveTab('processes')}
        >
          <Cpu size={18} />
          Processes
        </button>
        {user.is_admin && (
          <>
            <button
              className={`nav-item ${activeTab === 'terminal' ? 'active' : ''}`}
              onClick={() => setActiveTab('terminal')}
            >
              <TerminalIcon size={18} />
              Terminal
            </button>
            <button
              className={`nav-item ${activeTab === 'control' ? 'active' : ''}`}
              onClick={() => setActiveTab('control')}
            >
              <Settings size={18} />
              Control
            </button>
          </>
        )}
      </nav>

      {/* Main Content */}
      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            {/* System Info */}
            <div className="card system-info">
              <h3>System Information</h3>
              <div className="info-grid">
                <div className="info-item">
                  <Clock size={20} />
                  <div>
                    <div className="info-label">Uptime</div>
                    <div className="info-value">{formatUptime(metrics.uptime)}</div>
                  </div>
                </div>
                <div className="info-item">
                  <Cpu size={20} />
                  <div>
                    <div className="info-label">CPU Cores</div>
                    <div className="info-value">{metrics.cpu.count}</div>
                  </div>
                </div>
                <div className="info-item">
                  <Network size={20} />
                  <div>
                    <div className="info-label">Network RX</div>
                    <div className="info-value">
                      {formatBytes(metrics.network.bytes_recv)} GB
                    </div>
                  </div>
                </div>
                <div className="info-item">
                  <Network size={20} />
                  <div>
                    <div className="info-label">Network TX</div>
                    <div className="info-value">
                      {formatBytes(metrics.network.bytes_sent)} GB
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* CPU Section */}
            <div className="card metric-section">
              <div
                className="section-header"
                onClick={() => toggleSection('cpu')}
              >
                <h3>
                  <Cpu size={20} />
                  CPU Performance
                </h3>
                {expandedSections.cpu ? <ChevronUp /> : <ChevronDown />}
              </div>

              {expandedSections.cpu && (
                <div className="section-content">
                  <div className="metric-grid">
                    <div className="metric-card">
                      <Thermometer size={24} className={`icon-${getTempStatus(metrics.cpu.temperature)}`} />
                      <div className="metric-value">
                        {metrics.cpu.temperature}
                        <span className="metric-unit">°C</span>
                      </div>
                      <div className="metric-label">Temperature</div>
                    </div>

                    <div className="metric-card">
                      <Gauge size={24} />
                      <div className="metric-value">
                        {metrics.cpu.frequency}
                        <span className="metric-unit">MHz</span>
                      </div>
                      <div className="metric-label">Frequency</div>
                    </div>

                    <div className="metric-card">
                      <Activity size={24} className={`icon-${getStatusColor(metrics.cpu.percent)}`} />
                      <div className="metric-value">
                        {metrics.cpu.percent}
                        <span className="metric-unit">%</span>
                      </div>
                      <div className="metric-label">Usage</div>
                    </div>
                  </div>

                  <div className="cores-grid">
                    {metrics.cpu.per_core.map((usage, index) => (
                      <div key={`core-${index}`} className="core-item">
                        <div className="core-label">Core {index}</div>
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${usage}%` }}
                          ></div>
                        </div>
                        <div className="core-value">{usage}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Memory Section */}
            <div className="card metric-section">
              <div
                className="section-header"
                onClick={() => toggleSection('memory')}
              >
                <h3>
                  <MemoryStick size={20} />
                  Memory
                </h3>
                {expandedSections.memory ? <ChevronUp /> : <ChevronDown />}
              </div>

              {expandedSections.memory && (
                <div className="section-content">
                  <div className="metric-grid">
                    <div className="metric-card">
                      <MemoryStick size={24} className={`icon-${getStatusColor(metrics.memory.percent)}`} />
                      <div className="metric-value">
                        {metrics.memory.percent}
                        <span className="metric-unit">%</span>
                      </div>
                      <div className="metric-label">Used</div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-value">
                        {formatBytes(metrics.memory.used)}
                        <span className="metric-unit">GB</span>
                      </div>
                      <div className="metric-label">Used Memory</div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-value">
                        {formatBytes(metrics.memory.total)}
                        <span className="metric-unit">GB</span>
                      </div>
                      <div className="metric-label">Total Memory</div>
                    </div>
                  </div>

                  <div className="progress-bar-large">
                    <div
                      className="progress-fill"
                      style={{ width: `${metrics.memory.percent}%` }}
                    ></div>
                  </div>
                  <div className="progress-info">
                    <span>{formatBytes(metrics.memory.used)} GB used</span>
                    <span>{formatBytes(metrics.memory.available)} GB available</span>
                  </div>
                </div>
              )}
            </div>

            {/* Disk Section */}
            <div className="card metric-section">
              <div
                className="section-header"
                onClick={() => toggleSection('disk')}
              >
                <h3>
                  <HardDrive size={20} />
                  Disk Storage
                </h3>
                {expandedSections.disk ? <ChevronUp /> : <ChevronDown />}
              </div>

              {expandedSections.disk && (
                <div className="section-content">
                  <div className="metric-grid">
                    <div className="metric-card">
                      <HardDrive size={24} className={`icon-${getStatusColor(metrics.disk.percent)}`} />
                      <div className="metric-value">
                        {metrics.disk.percent}
                        <span className="metric-unit">%</span>
                      </div>
                      <div className="metric-label">Used</div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-value">
                        {formatBytes(metrics.disk.used)}
                        <span className="metric-unit">GB</span>
                      </div>
                      <div className="metric-label">Used Space</div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-value">
                        {formatBytes(metrics.disk.total)}
                        <span className="metric-unit">GB</span>
                      </div>
                      <div className="metric-label">Total Space</div>
                    </div>
                  </div>

                  <div className="progress-bar-large">
                    <div
                      className="progress-fill"
                      style={{ width: `${metrics.disk.percent}%` }}
                    ></div>
                  </div>
                  <div className="progress-info">
                    <span>{formatBytes(metrics.disk.used)} GB used</span>
                    <span>{formatBytes(metrics.disk.free)} GB free</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'charts' && (
          <div className="charts-view">
            <SystemChart history={history} />
          </div>
        )}

        {activeTab === 'processes' && (
          <div className="processes-view">
            <ProcessList />
          </div>
        )}

        {activeTab === 'terminal' && user.is_admin && (
          <div className="terminal-view">
            <Terminal />
          </div>
        )}

        {activeTab === 'control' && user.is_admin && (
          <div className="control-view">
            <SystemControls />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        <div className="footer-content">
          <span>Raspy Monitor v1.0</span>
          <span>•</span>
          <span>Last updated: {new Date(metrics.timestamp).toLocaleTimeString()}</span>
          <span>•</span>
          <span className="text-accent">raspy.gymms.space</span>
        </div>
      </footer>
    </div>
  );
}

export default Dashboard;
