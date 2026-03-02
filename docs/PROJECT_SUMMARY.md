# Raspy Monitor - Project Summary

## 🎯 What You Have

A complete, production-ready system monitoring dashboard for your Raspberry Pi 5 with:

### ✨ Features
- **Real-time monitoring** - CPU temp/freq/usage, RAM, disk, network stats
- **Historical charts** - Recharts visualizations with 1h/6h/24h views
- **Process management** - View top processes, sort by CPU/memory
- **Remote terminal** - Secure WebSocket shell access (admin only)
- **System controls** - CPU governor switching, system reboot
- **User authentication** - JWT-based login with role-based access
- **Beautiful UI** - Cyberpunk-industrial theme with animations

### 🔧 Tech Stack

**Backend (Python):**
- Flask web framework
- Flask-SocketIO for WebSockets
- Flask-JWT-Extended for auth
- psutil for system metrics
- SQLite database

**Frontend (React):**
- React 18 with Vite
- Recharts for data visualization
- Socket.IO client
- Lucide icons
- Custom CSS with cyberpunk theme

### 📁 What's Included

```
raspy-monitor.tar.gz contains:
├── backend/
│   ├── app.py                    # Flask API server (500+ lines)
│   ├── requirements.txt          # Python dependencies
│   └── [database created on first run]
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app with routing
│   │   ├── App.css              # Cyberpunk theme styles
│   │   ├── main.jsx             # Entry point
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login page
│   │   │   ├── Login.css
│   │   │   ├── Dashboard.jsx   # Main dashboard
│   │   │   └── Dashboard.css
│   │   └── components/
│   │       ├── SystemChart.jsx  # Historical data charts
│   │       ├── SystemChart.css
│   │       ├── ProcessList.jsx  # Process viewer
│   │       ├── ProcessList.css
│   │       ├── Terminal.jsx     # WebSocket terminal
│   │       ├── Terminal.css
│   │       ├── SystemControls.jsx # System settings
│   │       └── SystemControls.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── docs/
│   └── DEPLOYMENT.md            # Full deployment guide
│
├── README.md                     # Complete documentation
├── QUICKSTART.md                 # 5-minute setup guide
└── .gitignore
```

## 🚀 Recommended Subdomain

**raspy.gymms.space** ⭐ Best choice!

Why?
- Matches your hostname (raspy@k1taru)
- Clean and professional
- Clear purpose indication

Alternatives:
- monitor.gymms.space
- pi.gymms.space  
- stats.gymms.space

## 📊 Dashboard Tabs

1. **Overview** - Live system metrics with expandable sections
2. **Charts** - Historical data visualization (selectable metrics)
3. **Processes** - Top 20 processes with search and sorting
4. **Terminal** - Remote command execution (admin only)
5. **Control** - System management (CPU governor, reboot)

## 🔐 Security Features

- JWT authentication with 12-hour tokens
- Password hashing with Werkzeug
- Role-based access control (admin/user)
- Secure WebSocket connections
- Admin-only system controls
- Password change functionality

Default credentials (CHANGE IMMEDIATELY):
- Username: admin
- Password: admin123

## 🎨 UI Design

**Theme: Cyberpunk-Industrial**
- Dark backgrounds (#0a0e12)
- Neon green accents (#00ff88)
- Cyan highlights (#00d4ff)
- Monospace fonts (JetBrains Mono)
- Display fonts (Orbitron, Rajdhani)
- Animated grid background
- Scanline effect
- Glowing progress bars
- Hover animations

## ⚡ Performance

- Metrics collected every 60 seconds
- Frontend updates every 2 seconds
- History stored for 24 hours
- Top 20 processes tracked
- Efficient database queries
- Compressed assets

## 📦 Installation Steps

### Quick (Development)
```bash
# Extract archive
tar -xzf raspy-monitor.tar.gz
cd raspy-monitor

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### Production (with Cloudflare Tunnel)

See `docs/DEPLOYMENT.md` for:
- systemd service setup
- Nginx configuration
- Cloudflare Tunnel integration
- SSL/HTTPS setup
- Auto-start on boot
- Log rotation
- Backup strategy

## 🛠️ System Requirements

**Minimum:**
- Raspberry Pi 5 (8GB)
- Raspberry Pi OS (64-bit)
- Python 3.9+
- Node.js 18+
- 1GB free disk space

**Recommended:**
- Active cooling (fan)
- Dedicated network connection
- Regular backups
- UPS for power stability

## 🔧 Customization Ideas

### Easy:
- Change theme colors in App.css
- Adjust refresh intervals
- Modify metric collection frequency
- Add more processes to display
- Change history retention period

### Medium:
- Add new system metrics (GPU, USB devices)
- Implement user registration
- Add email notifications
- Create mobile app
- Add metric alerts

### Advanced:
- Multi-Pi monitoring
- Grafana integration
- Prometheus exporter
- Docker containerization
- Kubernetes deployment

## 📝 Configuration Files

### Backend Environment (.env)
```bash
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### Frontend Environment (.env)
```bash
VITE_API_URL=http://raspy.gymms.space:5000
```

### Nginx Config
- Reverse proxy for API
- WebSocket support
- Static file serving
- Gzip compression
- Security headers

### systemd Service
- Auto-start on boot
- Auto-restart on failure
- Proper logging
- Environment setup

## 🐛 Troubleshooting

Common issues and solutions in README.md:
- Backend won't start → Check port 5000
- Frontend build fails → Clear node_modules
- Can't change governor → Check sudo permissions
- WebSocket fails → Verify JWT token
- High CPU usage → Reduce refresh rate

## 📚 Documentation

- **README.md** - Main documentation (comprehensive)
- **QUICKSTART.md** - Get started in 5 minutes
- **DEPLOYMENT.md** - Production deployment guide
- **Code comments** - Inline explanations throughout

## 🎯 Next Steps

1. Extract the archive on your Pi
2. Follow QUICKSTART.md for initial setup
3. Test in development mode
4. Read DEPLOYMENT.md for production
5. Configure Cloudflare Tunnel
6. Change default password
7. Customize to your needs

## 🌟 Highlights

**What makes this special:**
- ✅ Production-ready code
- ✅ Beautiful, unique design
- ✅ Comprehensive documentation
- ✅ Security best practices
- ✅ Responsive mobile UI
- ✅ Easy to deploy
- ✅ Easy to extend

## 🔗 Integration with Existing Setup

Since you already have Cloudflare managing gymms.space:

1. Add subdomain to existing tunnel config
2. Or create new tunnel just for raspy monitor
3. Uses same Cloudflare account
4. Shares same DNS management
5. Gets automatic HTTPS
6. No port forwarding needed

## 💡 Pro Tips

1. **Use systemd** for auto-start reliability
2. **Enable log rotation** to save disk space
3. **Setup backups** for the database
4. **Monitor the monitor** with health checks
5. **Keep it updated** with Git
6. **Document changes** in a changelog
7. **Test before deploying** in dev mode

## 🎨 Design Choices

**Why this theme?**
- Distinctive and memorable
- Matches technical/system monitoring vibe
- High contrast for readability
- Professional yet modern
- Avoiding generic "AI slop" aesthetics

**Typography:**
- Orbitron/Rajdhani for headers (tech feel)
- JetBrains Mono for data (monospace clarity)
- Inter for body text (readable)

**Colors:**
- Dark background reduces eye strain
- Neon green for "online" status
- Cyan for secondary accents
- Red for warnings/errors

## 🚀 Deployment Timeline

Estimated time for full deployment:
- ☐ Initial setup: 30 minutes
- ☐ Testing: 15 minutes  
- ☐ systemd configuration: 15 minutes
- ☐ Nginx setup: 15 minutes
- ☐ Cloudflare Tunnel: 20 minutes
- ☐ SSL/security: 10 minutes
- ☐ Final testing: 15 minutes

**Total: ~2 hours** for production deployment

## ✨ You're Ready!

Everything you need is in the archive. Just extract, follow the guides, and you'll have a professional system monitor running on raspy.gymms.space in no time!

Questions? Check the comprehensive documentation in README.md and DEPLOYMENT.md.

Happy monitoring! 🎉
