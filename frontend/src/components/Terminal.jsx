import React, { useState, useEffect, useRef, useCallback } from 'react';
import io from 'socket.io-client';
import '../styles/Terminal.css';

const PROMPT = 'k1taru@raspy:~$';

function Terminal() {
  const [lines, setLines]         = useState([]);
  const [input, setInput]         = useState('');
  const [connected, setConnected] = useState(false);
  const [history, setHistory]     = useState([]);
  const [histIdx, setHistIdx]     = useState(-1);

  const socketRef = useRef(null);
  const bodyRef   = useRef(null);
  const inputRef  = useRef(null);
  const lineIdRef = useRef(0);

  const nextId = () => { lineIdRef.current += 1; return lineIdRef.current; };

  const push = useCallback((text, type = 'output') => {
    setLines(prev => [...prev, { id: nextId(), text, type }]);
  }, []);

  useEffect(() => {
    const token  = localStorage.getItem('token');

    socketRef.current = io(window.location.origin, { query: { token } });

    socketRef.current.on('connect', () => {
      setConnected(true);
      push(`Connected — ${new Date().toLocaleString()}`, 'info');
    });

    socketRef.current.on('disconnect', () => {
      setConnected(false);
      push('Connection closed.', 'error');
    });

    socketRef.current.on('connected', (data) => {
      push(data.message, 'info');
    });

    socketRef.current.on('terminal_output', (data) => {
      const raw = (data.output ?? '').replace(/\n$/, '');
      raw.split('\n').forEach(line => push(line, 'output'));
    });

    return () => socketRef.current?.disconnect();
  }, [push]);

  // Always scroll to bottom when output or input changes
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines, input]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const submit = () => {
    const cmd = input.trim();
    if (!cmd || !connected) return;

    push(`${PROMPT} ${cmd}`, 'cmd');

    if (cmd === 'clear') {
      setLines([]);
      setInput('');
      setHistIdx(-1);
      return;
    }

    socketRef.current.emit('terminal_input', { input: cmd });
    setHistory(prev => [cmd, ...prev.slice(0, 200)]);
    setHistIdx(-1);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHistIdx(prev => {
        const next = Math.min(prev + 1, history.length - 1);
        setInput(history[next] ?? '');
        return next;
      });
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHistIdx(prev => {
        const next = Math.max(prev - 1, -1);
        setInput(next === -1 ? '' : (history[next] ?? ''));
        return next;
      });
    } else if (e.key === 'c' && e.ctrlKey) {
      e.preventDefault();
      push(`${PROMPT} ${input}^C`, 'cmd');
      setInput('');
      setHistIdx(-1);
    }
  };

  return (
    <div className="xterm-window">
      {/* Title bar */}
      <div className="xterm-titlebar">
        <div className="xterm-dots">
          <span className="xterm-dot xterm-close" />
          <span className="xterm-dot xterm-minimize" />
          <span className="xterm-dot xterm-maximize" />
        </div>
        <span className="xterm-title">k1taru@raspy — bash</span>
        <div className="xterm-titlebar-right">
          <span className={`xterm-conn ${connected ? 'online' : 'offline'}`}>
            {connected ? '● connected' : '○ disconnected'}
          </span>
          <button className="xterm-clear-btn" onClick={() => setLines([])}>clear</button>
        </div>
      </div>

      {/* Body — click anywhere to focus input */}
      <div
        className="xterm-body"
        ref={bodyRef}
        onClick={() => inputRef.current?.focus()}
      >
        {lines.map(line => (
          <div key={line.id} className={`xterm-line xterm-${line.type}`}>
            <span className="xterm-text">{line.text}</span>
          </div>
        ))}

        {/* Live input line */}
        <div className="xterm-input-line">
          <span className="xterm-prompt">{PROMPT}&nbsp;</span>
          <input
            ref={inputRef}
            className="xterm-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!connected}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck={false}
          />
        </div>
      </div>
    </div>
  );
}

export default Terminal;
