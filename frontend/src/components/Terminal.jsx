import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import { Terminal as TerminalIcon, Send, AlertTriangle } from 'lucide-react';
import './Terminal.css';

function Terminal() {
  const [output, setOutput] = useState([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  const outputRef = useRef(null);
  const lineIdRef = useRef(0);

  const nextId = () => { lineIdRef.current += 1; return lineIdRef.current; };

  useEffect(() => {
    const token = localStorage.getItem('token');
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    
    // Connect to WebSocket with JWT token
    socketRef.current = io(apiUrl, {
      query: { token }
    });

    socketRef.current.on('connect', () => {
      setConnected(true);
      addOutput('System terminal connected.', 'system');
      addOutput('Type commands and press Enter or click Send.', 'system');
    });

    socketRef.current.on('disconnect', () => {
      setConnected(false);
      addOutput('Disconnected from terminal.', 'error');
    });

    socketRef.current.on('connected', (data) => {
      addOutput(data.message, 'system');
    });

    socketRef.current.on('terminal_output', (data) => {
      addOutput(data.output, 'output');
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const addOutput = (text, type = 'output') => {
    setOutput(prev => [...prev, {
      id: nextId(),
      text,
      type,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!input.trim() || !connected) return;

    addOutput(`$ ${input}`, 'input');
    
    socketRef.current.emit('terminal_input', {
      input: input.trim()
    });

    setInput('');
  };

  const clearTerminal = () => {
    setOutput([]);
  };

  return (
    <div className="card terminal-container">
      <div className="terminal-header">
        <h2>
          <TerminalIcon size={24} />
          Remote Terminal
        </h2>

        <div className="terminal-controls">
          <div className="connection-status">
            <span className={`status-dot ${connected ? 'online' : 'danger'}`}></span>
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <button 
            className="btn btn-secondary" 
            onClick={clearTerminal}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="warning-banner">
        <AlertTriangle size={16} />
        <span>Warning: Commands execute with current user privileges. Use with caution.</span>
      </div>

      <div className="terminal-output" ref={outputRef}>
        {output.map((line) => (
          <div key={line.id} className={`terminal-line ${line.type}`}>
            {line.type === 'input' && <span className="prompt">→ </span>}
            {line.type === 'system' && <span className="system-prefix">[SYSTEM] </span>}
            {line.type === 'error' && <span className="error-prefix">[ERROR] </span>}
            <span className="terminal-text">{line.text}</span>
          </div>
        ))}
        
        {output.length === 0 && (
          <div className="terminal-welcome">
            <p>╔══════════════════════════════════════╗</p>
            <p>║   RASPY MONITOR REMOTE TERMINAL     ║</p>
            <p>║   Secure Shell Access v1.0          ║</p>
            <p>╚══════════════════════════════════════╝</p>
            <p></p>
            <p>Type your commands below...</p>
          </div>
        )}
      </div>

      <form className="terminal-input-container" onSubmit={handleSubmit}>
        <span className="terminal-prompt">$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter command..."
          disabled={!connected}
          className="terminal-input"
          autoComplete="off"
          spellCheck="false"
        />
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={!connected || !input.trim()}
        >
          <Send size={16} />
          Send
        </button>
      </form>

      <div className="terminal-footer">
        <p className="text-muted">
          Common commands: <code>ls</code>, <code>pwd</code>, <code>top</code>, 
          <code>df -h</code>, <code>free -h</code>, <code>uptime</code>
        </p>
      </div>
    </div>
  );
}

export default Terminal;
