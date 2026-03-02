# Deployment Guide for Raspy Monitor

This guide covers deploying Raspy Monitor on your Raspberry Pi 5 with Cloudflare Tunnel integration.

## Recommended Subdomain

**raspy.gymms.space** - Clean, matches your hostname, and clearly indicates the purpose.

Alternative options:
- monitor.gymms.space
- pi.gymms.space
- stats.gymms.space

## Quick Deployment Steps

### 1. Prepare Your Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nodejs npm nginx git

# Verify versions
python3 --version  # Should be 3.9+
node --version     # Should be 18+
```

### 2. Clone and Setup Backend

```bash
# Clone repository (replace with your repo URL)
cd ~
git clone <your-repo-url> raspy-monitor
cd raspy-monitor/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate secure secret keys
python3 -c "import os; print('SECRET_KEY:', os.urandom(24).hex())"
python3 -c "import os; print('JWT_SECRET_KEY:', os.urandom(24).hex())"
```

Edit `app.py` and replace the secret keys with the generated ones:
```python
app.config['SECRET_KEY'] = 'your-generated-secret-key'
app.config['JWT_SECRET_KEY'] = 'your-generated-jwt-secret-key'
```

### 3. Setup Backend Service

Create systemd service:
```bash
sudo nano /etc/systemd/system/raspy-monitor-backend.service
```

Content:
```ini
[Unit]
Description=Raspy Monitor Backend API
After=network.target

[Service]
Type=simple
User=raspy
WorkingDirectory=/home/raspy/raspy-monitor/backend
Environment="PATH=/home/raspy/raspy-monitor/backend/venv/bin"
ExecStart=/home/raspy/raspy-monitor/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable raspy-monitor-backend
sudo systemctl start raspy-monitor-backend
sudo systemctl status raspy-monitor-backend
```

### 4. Setup Sudo Permissions

Create sudoers file:
```bash
sudo visudo -f /etc/sudoers.d/raspy-monitor
```

Add:
```
raspy ALL=(ALL) NOPASSWD: /bin/sh -c echo * > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
raspy ALL=(ALL) NOPASSWD: /sbin/reboot
```

Test:
```bash
sudo echo "performance" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### 5. Build Frontend

```bash
cd ~/raspy-monitor/frontend

# Install dependencies
npm install

# Create production environment file
cat > .env << EOF
VITE_API_URL=http://raspy.gymms.space:5000
EOF

# Build for production
npm run build
```

### 6. Configure Nginx

Install nginx if not already installed:
```bash
sudo apt install nginx -y
```

Create site configuration:
```bash
sudo nano /etc/nginx/sites-available/raspy-monitor
```

Content:
```nginx
server {
    listen 80;
    server_name raspy.gymms.space;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend static files
    root /home/raspy/raspy-monitor/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket proxy for terminal
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/raspy-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7. Setup Cloudflare Tunnel

Since you already have `gymms.space` with Cloudflare:

**Option A: Using Existing Tunnel**

If you already have a cloudflare service running:

1. Edit your existing Cloudflare Tunnel config:
```bash
sudo nano /etc/cloudflared/config.yml
```

2. Add new ingress rule BEFORE the catch-all rule:
```yaml
ingress:
  - hostname: raspy.gymms.space
    service: http://localhost:80
  - hostname: www.gymms.space
    service: http://localhost:8080  # Your existing service
  - service: http_status:404
```

3. Restart cloudflared:
```bash
sudo systemctl restart cloudflared
```

4. Add DNS record in Cloudflare Dashboard:
   - Go to DNS settings for gymms.space
   - Add CNAME record:
     - Name: `raspy`
     - Target: `<your-tunnel-id>.cfargotunnel.com`
     - Proxy status: Proxied

**Option B: Create New Tunnel**

1. Install cloudflared (if not installed):
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```

2. Authenticate:
```bash
cloudflared tunnel login
```

3. Create tunnel:
```bash
cloudflared tunnel create raspy-monitor
```

4. Create config:
```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Content:
```yaml
tunnel: <tunnel-id-from-step-3>
credentials-file: /home/raspy/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: raspy.gymms.space
    service: http://localhost:80
  - service: http_status:404
```

5. Route DNS:
```bash
cloudflared tunnel route dns raspy-monitor raspy.gymms.space
```

6. Install as service:
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### 8. Verify Deployment

1. **Check backend status:**
```bash
sudo systemctl status raspy-monitor-backend
curl http://localhost:5000/api/health
```

2. **Check nginx:**
```bash
sudo systemctl status nginx
curl http://localhost/
```

3. **Check cloudflare tunnel:**
```bash
sudo systemctl status cloudflared
```

4. **Access the application:**
   - Open browser to: `https://raspy.gymms.space`
   - Login with: `admin` / `admin123`
   - **IMMEDIATELY change the password!**

## Post-Deployment Tasks

### 1. Change Default Password
- Login to the dashboard
- Go to settings/profile (you may need to add this feature)
- Change from `admin123` to a strong password

### 2. Update .env Files
Store secret keys securely, not in the code:

```bash
# Backend - create .env file
cd ~/raspy-monitor/backend
cat > .env << EOF
SECRET_KEY=your-generated-secret-key
JWT_SECRET_KEY=your-generated-jwt-secret-key
EOF

# Update app.py to read from environment
# Add to top of app.py:
from dotenv import load_dotenv
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
```

Install python-dotenv:
```bash
source venv/bin/activate
pip install python-dotenv
```

### 3. Setup Automatic Updates

Create update script:
```bash
nano ~/update-raspy-monitor.sh
```

Content:
```bash
#!/bin/bash
cd ~/raspy-monitor
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart raspy-monitor-backend

# Update frontend
cd ../frontend
npm install
npm run build

# Restart nginx
sudo systemctl restart nginx

echo "Update complete!"
```

Make executable:
```bash
chmod +x ~/update-raspy-monitor.sh
```

### 4. Setup Log Rotation

Create logrotate config:
```bash
sudo nano /etc/logrotate.d/raspy-monitor
```

Content:
```
/home/raspy/raspy-monitor/backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 5. Monitor System Health

Add monitoring script:
```bash
nano ~/monitor-health.sh
```

Content:
```bash
#!/bin/bash
# Check if backend is running
if ! systemctl is-active --quiet raspy-monitor-backend; then
    echo "Backend is down! Restarting..."
    sudo systemctl start raspy-monitor-backend
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "Nginx is down! Restarting..."
    sudo systemctl start nginx
fi

# Check if cloudflared is running
if ! systemctl is-active --quiet cloudflared; then
    echo "Cloudflared is down! Restarting..."
    sudo systemctl start cloudflared
fi
```

Add to crontab:
```bash
chmod +x ~/monitor-health.sh
crontab -e

# Add:
*/5 * * * * /home/raspy/monitor-health.sh >> /home/raspy/monitor.log 2>&1
```

## Firewall Configuration (Optional)

If you're using ufw:

```bash
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (for local access)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

Note: Cloudflare Tunnel doesn't require opening ports since it creates outbound connections.

## Troubleshooting

### Backend not starting
```bash
# Check logs
sudo journalctl -u raspy-monitor-backend -f

# Check if port 5000 is in use
sudo lsof -i :5000

# Test manually
cd ~/raspy-monitor/backend
source venv/bin/activate
python app.py
```

### Frontend not loading
```bash
# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify build exists
ls -la ~/raspy-monitor/frontend/dist

# Test nginx config
sudo nginx -t
```

### Cloudflare Tunnel issues
```bash
# Check tunnel status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f

# Test tunnel connectivity
cloudflared tunnel info <tunnel-name>
```

## Maintenance Commands

```bash
# Restart all services
sudo systemctl restart raspy-monitor-backend nginx cloudflared

# View all logs
sudo journalctl -u raspy-monitor-backend -u nginx -u cloudflared -f

# Check system resources
htop

# Check disk space
df -h

# Check database size
du -h ~/raspy-monitor/backend/raspy_monitor.db
```

## Backup Strategy

Create backup script:
```bash
nano ~/backup-raspy-monitor.sh
```

Content:
```bash
#!/bin/bash
BACKUP_DIR=~/backups/raspy-monitor
mkdir -p $BACKUP_DIR

# Backup database
cp ~/raspy-monitor/backend/raspy_monitor.db $BACKUP_DIR/raspy_monitor_$(date +%Y%m%d).db

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

Run daily:
```bash
chmod +x ~/backup-raspy-monitor.sh
crontab -e

# Add:
0 2 * * * /home/raspy/backup-raspy-monitor.sh
```

## Performance Optimization

### 1. Reduce Metric Collection Frequency

Edit `app.py`:
```python
# Change from 60 seconds to 120 seconds
time.sleep(120)  # Store metrics every 2 minutes
```

### 2. Limit History Storage

Edit `app.py`:
```python
# Keep only 12 hours of data instead of 24
cutoff = datetime.now() - timedelta(hours=12)
```

### 3. Enable Nginx Caching

Add to nginx config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/metrics {
    proxy_cache api_cache;
    proxy_cache_valid 200 5s;
    # ... other proxy settings
}
```

---

You're all set! Access your dashboard at **https://raspy.gymms.space**
