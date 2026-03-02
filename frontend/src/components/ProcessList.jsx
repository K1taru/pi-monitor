import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Search, RefreshCw } from 'lucide-react';
import './ProcessList.css';

function ProcessList() {
  const [processes, setProcesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('cpu');

  const fetchProcesses = async () => {
    try {
      const response = await axios.get('/api/processes');
      setProcesses(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching processes:', error);
    }
  };

  useEffect(() => {
    fetchProcesses();
    const interval = setInterval(fetchProcesses, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredProcesses = processes
    .filter(proc => 
      proc.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'cpu') return b.cpu - a.cpu;
      if (sortBy === 'memory') return b.memory - a.memory;
      return 0;
    });

  if (loading) {
    return (
      <div className="card">
        <div className="loading-spinner"></div>
        <p className="text-center">Loading processes...</p>
      </div>
    );
  }

  return (
    <div className="card process-list-container">
      <div className="process-header">
        <h2>
          <Activity size={24} />
          Running Processes
        </h2>
        
        <div className="process-controls">
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search processes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <button className="btn btn-secondary" onClick={fetchProcesses}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      <div className="sort-buttons">
        <button
          className={`sort-btn ${sortBy === 'cpu' ? 'active' : ''}`}
          onClick={() => setSortBy('cpu')}
        >
          Sort by CPU
        </button>
        <button
          className={`sort-btn ${sortBy === 'memory' ? 'active' : ''}`}
          onClick={() => setSortBy('memory')}
        >
          Sort by Memory
        </button>
      </div>

      <div className="process-table-container">
        <table className="process-table">
          <thead>
            <tr>
              <th>PID</th>
              <th>Process Name</th>
              <th>CPU %</th>
              <th>Memory %</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredProcesses.map((proc) => (
              <tr key={proc.pid}>
                <td className="pid-cell">{proc.pid}</td>
                <td className="name-cell">{proc.name}</td>
                <td className="metric-cell">
                  <div className="metric-bar-container">
                    <div 
                      className="metric-bar cpu-bar"
                      style={{ width: `${Math.min(proc.cpu, 100)}%` }}
                    ></div>
                    <span>{proc.cpu}%</span>
                  </div>
                </td>
                <td className="metric-cell">
                  <div className="metric-bar-container">
                    <div 
                      className="metric-bar memory-bar"
                      style={{ width: `${Math.min(proc.memory, 100)}%` }}
                    ></div>
                    <span>{proc.memory}%</span>
                  </div>
                </td>
                <td className="status-cell">
                  <span className="status-badge running">Running</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredProcesses.length === 0 && (
        <div className="no-results">
          <p>No processes found matching "{searchTerm}"</p>
        </div>
      )}

      <div className="process-footer">
        <p>Showing top {filteredProcesses.length} processes</p>
      </div>
    </div>
  );
}

export default ProcessList;
