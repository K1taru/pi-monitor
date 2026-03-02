# Quick Start Guide

## TL;DR - Get Running in 5 Minutes

### 1. Install Dependencies (1 min)
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm nginx
```

### 2. Setup Backend (2 min)
```bash
cd ~/raspy-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Change secret keys in app.py!
python app.py  # Test it works
```

### 3. Setup Frontend (2 min)
```bash
cd ~/raspy-monitor/frontend
npm install
npm run dev  # Development mode
```

### 4. Access Dashboard
Open browser: `http://localhost:3000`
Login: `admin` / `admin123`

**CHANGE PASSWORD IMMEDIATELY!**

## Recommended Subdomain

🎯 **raspy.gymms.space** - Perfect choice!

Matches your hostname (raspy@k1taru) and clearly indicates it's for the Raspberry Pi.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            Cloudflare Tunnel                     │
│         raspy.gymms.space (HTTPS)               │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│               Nginx (Port 80)                    │
│  ┌─────────────────┬──────────────────────────┐ │
│  │   Static Files  │    Proxy /api & /socket  │ │
│  │  (React Build)  │                          │ │
│  └────────┬────────┴───────────┬──────────────┘ │
└───────────┼────────────────────┼─────────────────┘
            │                    │
            ↓                    ↓
    ┌──────────────┐    ┌──────────────────────┐
    │   Frontend   │    │   Flask Backend      │
    │   (React)    │    │   (Port 5000)        │
    │              │    │                      │
    │  - Dashboard │    │  - REST API          │
    │  - Charts    │    │  - WebSocket         │
    │  - Terminal  │    │  - System Metrics    │
    └──────────────┘    │  - Authentication    │
                        └──────────────────────┘
                                 │
                                 ↓
                        ┌──────────────────┐
                        │  Raspberry Pi    │
                        │  System (psutil) │
                        └──────────────────┘
```

## Key Features at a Glance

| Feature | Description | Access |
|---------|-------------|--------|
| 📊 Real-time Metrics | CPU, RAM, Disk, Temp | All Users |
| 📈 Historical Charts | 1h, 6h, 24h trends | All Users |
| 💻 Remote Terminal | Execute commands | Admin Only |
| ⚙️ System Control | CPU governor, reboot | Admin Only |
| 🔒 Authentication | JWT-based security | Required |
| 📱 Responsive UI | Works on mobile | All Users |

## Default Credentials

⚠️ **CRITICAL: Change immediately!**

- Username: `admin`
- Password: `admin123`

## What to Do After First Login

1. ✅ Change password
2. ✅ Test all dashboard tabs
3. ✅ Check terminal access (if admin)
4. ✅ Verify system controls work
5. ✅ Setup automatic startup (systemd)
6. ✅ Configure Cloudflare Tunnel
7. ✅ Enable HTTPS

## File Locations

```
~/raspy-monitor/
├── backend/
│   ├── app.py              ← Main backend code
│   ├── requirements.txt    ← Python packages
│   └── raspy_monitor.db    ← User database (auto-created)
│
├── frontend/
│   ├── src/                ← React source code
│   ├── dist/               ← Production build (after npm run build)
│   └── package.json        ← Node packages
│
├── docs/
│   └── DEPLOYMENT.md       ← Full deployment guide
│
└── README.md               ← Main documentation
```

## Common Commands

### Development
```bash
# Start backend
cd ~/raspy-monitor/backend && source venv/bin/activate && python app.py

# Start frontend (different terminal)
cd ~/raspy-monitor/frontend && npm run dev
```

### Production
```bash
# Build frontend
cd ~/raspy-monitor/frontend && npm run build

# Restart services
sudo systemctl restart raspy-monitor-backend nginx
```

### Monitoring
```bash
# Check backend status
sudo systemctl status raspy-monitor-backend

# View backend logs
sudo journalctl -u raspy-monitor-backend -f

# Check nginx
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Updates
```bash
cd ~/raspy-monitor
git pull
~/update-raspy-monitor.sh  # If you created the update script
```

## Security Checklist

- [ ] Changed default password
- [ ] Updated secret keys in app.py
- [ ] Setup HTTPS via Cloudflare
- [ ] Limited terminal access to admins only
- [ ] Configured firewall (optional)
- [ ] Setup log rotation
- [ ] Enable automatic backups

## Next Steps

1. **Read the full README** for detailed features
2. **Check DEPLOYMENT.md** for production setup
3. **Customize the theme** by editing App.css
4. **Add more metrics** by extending app.py
5. **Setup monitoring** with health check scripts

## Support

- 📖 Full docs: `README.md`
- 🚀 Deployment: `docs/DEPLOYMENT.md`
- 🐛 Issues: Check logs and troubleshooting section
- 💬 Questions: Review code comments

## Tips

💡 **CPU Temperature High?**
- Switch to "powersave" governor when idle
- Ensure good ventilation
- Consider a heatsink or fan

💡 **Want Faster Updates?**
- Reduce refresh interval in Dashboard.jsx
- Note: This increases CPU usage

💡 **Need More History?**
- Increase retention in app.py cleanup_old_metrics()
- Note: This increases database size

💡 **Mobile Access?**
- The UI is fully responsive
- Works great on phones and tablets

---

🎉 **You're ready to monitor your Raspberry Pi like a pro!**
