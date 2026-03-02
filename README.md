# Pi Monitor

Real-time system monitoring dashboard for Raspberry Pi 5.

Live at **[raspy.gymms.space](https://raspy.gymms.space)**

## What it does

- CPU temperature, frequency, per-core usage
- Memory & disk stats
- Network I/O counters
- Historical charts (1h / 6h / 24h)
- Top processes list
- Remote terminal (admin)
- CPU governor control & reboot (admin)
- JWT authentication

## Stack

| Layer | Tech |
|-------|------|
| Backend | Flask, Flask-SocketIO, Flask-JWT-Extended, psutil, SQLite |
| Frontend | React 18, Vite, Recharts, Socket.IO, Lucide |
| Tunnel | Cloudflared → `https://raspy.gymms.space` |

## Project structure

```
pi-monitor/
├── backend/
│   ├── app.py              # Entry point (factory pattern)
│   ├── config.py            # Reads .env secrets
│   ├── extensions.py        # SocketIO + JWT instances
│   ├── database.py          # SQLite helpers
│   ├── metrics.py           # psutil collectors + background thread
│   ├── decorators.py        # admin_required
│   ├── routes/
│   │   ├── auth.py          # /api/auth/*
│   │   ├── metrics.py       # /api/metrics/*, /api/processes
│   │   ├── system.py        # /api/system/* (governor, reboot)
│   │   └── frontend.py      # SPA catch-all + /api/health
│   ├── sockets/
│   │   └── terminal.py      # WebSocket terminal
│   ├── requirements.txt
│   └── .env                 # secrets (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/           # Login, Dashboard
│   │   └── components/      # Terminal, SystemChart, ProcessList, SystemControls
│   ├── package.json
│   ├── vite.config.js
│   └── .env                 # VITE_API_URL (gitignored)
├── deploy/
│   ├── raspy-monitor.service    # systemd unit
│   └── raspy-monitor-sudoers    # passwordless governor + reboot
└── docs/
    └── SETUP.md                 # Full manual setup guide
```

## Quick start

See [docs/SETUP.md](docs/SETUP.md) for the full step-by-step guide.

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Create .env with SECRET_KEY, JWT_SECRET_KEY, PORT=8001, CORS_ORIGINS
python app.py

# Frontend
cd frontend
echo "VITE_API_URL=https://raspy.gymms.space" > .env
npm ci && npm run build
```

## Default credentials

`admin` / `admin123` — **change immediately after first login.**

## License

MIT
