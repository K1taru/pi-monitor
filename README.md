# Raspy Monitor - Raspberry Pi System Monitor

A real-time system monitoring and management dashboard for Raspberry Pi 5, featuring:

- 🔒 Secure JWT authentication
- 📊 Real-time system metrics (CPU, RAM, Disk, Temperature)
- 📈 Historical data charts
- 💻 Remote terminal access (admin only)
- ⚙️ System controls (CPU governor, etc.)
- 🎨 Cyberpunk-industrial themed UI

## Features

### Monitoring
- CPU temperature, frequency, and usage per core
- Memory usage and availability
- Disk usage and free space
- Network statistics (bytes sent/received)
- System uptime
- Top processes by CPU and memory

### Administration (Admin Users Only)
- Remote terminal via WebSocket
- CPU performance profile switching
- System reboot capability
- Fan control (requires additional setup)

### Security
- JWT-based authentication
- Role-based access control (admin/user)
- Secure WebSocket connections
- Password change functionality

## Tech Stack

**Backend:**
- Flask (Python web framework)
- Flask-SocketIO (WebSocket support)
- Flask-JWT-Extended (authentication)
- psutil (system metrics)
- SQLite (user database)

**Frontend:**
- React 18
- Vite (build tool)
- Recharts (data visualization)
- Socket.IO client (WebSocket)
- Lucide React (icons)

## Installation

### Prerequisites

- Raspberry Pi 5 (8GB) with Raspberry Pi OS
- Python 3.9+
- Node.js 18+ and npm
- Git

### Backend Setup

1. **Clone the repository:**
```bash
cd ~
git clone <your-repo-url> raspy-monitor
cd raspy-monitor/backend
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure the application:**

Edit `app.py` and change the secret keys:
```python
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key-here'  # Change this!
```

5. **Set up sudo permissions (for system controls):**

Create a sudoers file for the Flask user:
```bash
sudo visudo -f /etc/sudoers.d/raspy-monitor
```

Add these lines (replace `youruser` with your username):
```
youruser ALL=(ALL) NOPASSWD: /bin/sh -c echo * > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
youruser ALL=(ALL) NOPASSWD: /sbin/reboot
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd ~/raspy-monitor/frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure API endpoint:**

Create `.env` file:
```bash
VITE_API_URL=http://raspy.gymms.space:5000
```

For development, you can use:
```bash
VITE_API_URL=http://localhost:5000
```

4. **Build for production:**
```bash
npm run build
```

## Running the Application

### Development Mode

**Backend (Terminal 1):**
```bash
cd ~/raspy-monitor/backend
source venv/bin/activate
python app.py
```

**Frontend (Terminal 2):**
```bash
cd ~/raspy-monitor/frontend
npm run dev
```

Access at: `http://localhost:3000`

### Production Deployment

#### Option 1: Using systemd services

1. **Create backend service:**

```bash
sudo nano /etc/systemd/system/raspy-monitor-backend.service
```

Add:
```ini
[Unit]
Description=Raspy Monitor Backend
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/raspy-monitor/backend
Environment="PATH=/home/youruser/raspy-monitor/backend/venv/bin"
ExecStart=/home/youruser/raspy-monitor/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Start backend service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable raspy-monitor-backend
sudo systemctl start raspy-monitor-backend
```

3. **Serve frontend with nginx:**

Install nginx:
```bash
sudo apt install nginx
```

Create nginx config:
```bash
sudo nano /etc/nginx/sites-available/raspy-monitor
```

Add:
```nginx
server {
    listen 80;
    server_name raspy.gymms.space;

    # Frontend
    root /home/youruser/raspy-monitor/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/raspy-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Option 2: Using Cloudflare Tunnel

Since you already have Cloudflare managing gymms.space:

1. **Install Cloudflare Tunnel:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```

2. **Authenticate:**
```bash
cloudflared tunnel login
```

3. **Create tunnel:**
```bash
cloudflared tunnel create raspy-monitor
```

4. **Configure tunnel:**

Create `~/.cloudflared/config.yml`:
```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/youruser/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: raspy.gymms.space
    service: http://localhost:80
  - service: http_status:404
```

5. **Add DNS record:**
```bash
cloudflared tunnel route dns raspy-monitor raspy.gymms.space
```

6. **Run tunnel as service:**
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

## Default Credentials

**⚠️ IMPORTANT: Change immediately after first login!**

- Username: `admin`
- Password: `admin123`

Change password from the dashboard after logging in.

## Usage

### Login
1. Navigate to `http://raspy.gymms.space` (or your configured domain)
2. Login with credentials
3. **Change the default password immediately!**

### Dashboard Tabs

**Overview:**
- Real-time system metrics
- CPU temperature and frequency
- Memory and disk usage
- Per-core CPU usage

**Charts:**
- Historical data visualization
- Toggle different metrics
- Adjust time range (1h, 6h, 24h)

**Processes:**
- View running processes
- Sort by CPU or memory
- Search by process name

**Terminal (Admin):**
- Execute shell commands remotely
- View command output
- Secure WebSocket connection

**Control (Admin):**
- Change CPU governor (performance profile)
- Reboot system
- Future: Fan control

## Security Considerations

1. **Change default credentials** immediately
2. **Use HTTPS** in production (Cloudflare provides this automatically)
3. **Firewall rules**: Only expose necessary ports
4. **Keep dependencies updated**: Regularly update both backend and frontend packages
5. **Limit terminal access**: Only trusted admins should have terminal access
6. **Monitor logs**: Check system logs regularly for suspicious activity

## Troubleshooting

### Backend won't start
- Check if port 5000 is available: `sudo lsof -i :5000`
- Check logs: `sudo journalctl -u raspy-monitor-backend -f`
- Verify Python dependencies: `pip list`

### Frontend build fails
- Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
- Check Node version: `node --version` (should be 18+)

### Can't change CPU governor
- Check sudo permissions: `sudo -l`
- Verify sudoers file exists: `/etc/sudoers.d/raspy-monitor`

### WebSocket connection fails
- Check if backend is running
- Verify JWT token is valid
- Check browser console for errors

### High CPU usage
- Reduce metric collection frequency in `app.py`
- Adjust frontend refresh intervals

## Development

### Adding new metrics
1. Add collection logic in `backend/app.py`
2. Create corresponding frontend component
3. Update database schema if needed

### Customizing theme
- Edit `frontend/src/App.css` for color variables
- Modify component CSS files for specific elements

### Adding new system controls
1. Add API endpoint in `backend/app.py`
2. Create UI in `frontend/src/components/SystemControls.jsx`
3. Update sudo permissions if needed

## File Structure

```
raspy-monitor/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── raspy_monitor.db    # SQLite database (auto-created)
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
└── docs/                   # Documentation
```

## License

MIT License - feel free to modify and use for your own projects!

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
- Check the troubleshooting section
- Review system logs
- Open an issue on GitHub

---

**Built with ❤️ for Raspberry Pi enthusiasts**
