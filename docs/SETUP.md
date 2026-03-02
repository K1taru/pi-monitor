# Pi Monitor — Setup Guide

This guide covers installation on a Raspberry Pi (or any Linux system) with proper user/home directory support and multi-user capability.

---

## Quick Start (Recommended)

For most users, run the automated setup script:

```bash
# On the Pi as root:
cd ~<username>/pi-monitor  # or wherever you cloned it
sudo setup/setup.sh <username>

# Example:
sudo setup/setup.sh k1taru
```

The script will:
1. Create Python venv and install dependencies
2. Build the frontend
3. Install system binaries (`pi-monitor-fan-control`, `pi-monitor-gov-control`)
4. Install sudoers configuration
5. Create a systemd service
6. Initialize the database with users from `.env`

Then start the service:
```bash
sudo systemctl start pi-monitor-k1taru
sudo systemctl status pi-monitor-k1taru
```

---

## Manual Setup (Step-by-Step)

If you prefer to set up manually, follow these steps:

### 1. Clone and prepare

```bash
cd ~
git clone <your-repo-url> pi-monitor
cd pi-monitor
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Generate secrets for .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### 3. Create `.env` with users

Copy `.env.example` and customize:

```bash
cp .env.example .env
```

Edit `backend/.env`:

```dotenv
SECRET_KEY=<generated-above>
JWT_SECRET_KEY=<generated-above>
PORT=8001
CORS_ORIGINS=https://raspy.gymms.space,http://localhost:3000

# Define users to create on startup
# Format: username:password:is_admin;username:password:is_admin
DEFAULT_USERS=k1taru:mypassword:1;guest:guestpass:0
```

### 4. Frontend setup

```bash
cd frontend
npm ci
npm run build
```

### 5. System binaries and sudoers

```bash
# Install the wrapper scripts (live in backend/scripts/)
sudo install -m 0755 ~/pi-monitor/backend/scripts/fan-control.sh /usr/local/bin/pi-monitor-fan-control
sudo install -m 0755 ~/pi-monitor/backend/scripts/gov-control.sh /usr/local/bin/pi-monitor-gov-control

# Create sudoers configuration for your user (replace 'k1taru' with your username)
sudo tee /etc/sudoers.d/pi-monitor-k1taru > /dev/null << 'EOF'
k1taru ALL=(root) NOPASSWD: /usr/local/bin/pi-monitor-gov-control
k1taru ALL=(root) NOPASSWD: /usr/local/bin/pi-monitor-fan-control
k1taru ALL=(root) NOPASSWD: /usr/sbin/reboot
EOF

sudo chmod 0440 /etc/sudoers.d/pi-monitor-k1taru
sudo visudo -c  # verify no errors
```

### 6. Database initialization

```bash
cd ~/pi-monitor/backend
source venv/bin/activate

# Initialize database with users from .env
./../../setup/init-users.sh
```

Or manually with Python:
```bash
python3 -c "from database import init_db; init_db()"
```

### 7. Systemd service

Create `/etc/systemd/system/pi-monitor-k1taru.service`:

```ini
[Unit]
Description=Raspberry Pi Monitor Backend (k1taru)
After=network.target

[Service]
Type=simple
User=k1taru
WorkingDirectory=/home/k1taru/pi-monitor/backend

EnvironmentFile=/home/k1taru/pi-monitor/backend/.env

ExecStart=/home/k1taru/pi-monitor/backend/venv/bin/python app.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-monitor-k1taru
sudo systemctl start pi-monitor-k1taru
```

---

## User Management

### Reset users from `.env`

If you need to reinitialize the user database from your `.env` file:

```bash
cd ~/pi-monitor/backend
source venv/bin/activate
../../setup/init-users.sh
```

Or to completely reset (delete old DB):
```bash
../../setup/init-users.sh --reset
```

### Change user password at runtime

```bash
curl -X POST https://raspy.gymms.space/api/auth/change-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"current","new_password":"newpassword"}'
```

---

## Multi-User Setup

You can run multiple instances for different users on the same Pi:

1. For each user, run:
   ```bash
   sudo setup/setup.sh <username>
   ```

2. Each user gets:
   - Their own systemd service: `pi-monitor-<username>`
   - Their own `.env` file (different SECRET_KEY, PORT, users, etc.)
   - Their own sudoers entry: `/etc/sudoers.d/pi-monitor-<username>`

3. Start services independently:
   ```bash
   sudo systemctl start pi-monitor-k1taru
   sudo systemctl start pi-monitor-guest
   ```

Just make sure each user's `.env` uses a different PORT if running locally.

---

## Cloudflared Tunnel (Optional)

> Already configured to tunnel `https://raspy.gymms.space` → `localhost:8001`.

If not set up yet:

```bash
# Install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Authenticate & create tunnel
cloudflared tunnel login
cloudflared tunnel create pi-monitor

# Configure ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /home/k1taru/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: raspy.gymms.space
    service: http://localhost:8001
  - service: http_status:404

# DNS + service
cloudflared tunnel route dns pi-monitor raspy.gymms.space
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## Post-Install

1. Open `https://raspy.gymms.space` (or `http://localhost:8001` locally)
2. Login with credentials from `DEFAULT_USERS` in `.env`
3. **Change passwords immediately** via the Control panel
4. Verify all features work: Overview, Charts, Processes, Terminal, Control

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Script says user not found | Verify user exists: `id username`; check home dir: `ls ~username` |
| "Permission denied" when running setup.sh | Must run with sudo: `sudo setup/setup.sh k1taru` |
| Service won't start | `sudo journalctl -u pi-monitor-k1taru -n 50 --no-pager` |
| Port in use | `sudo lsof -i :8001`; pick different port in `.env` |
| Login fails with "Invalid credentials" | Check users in DB: `sqlite3 backend/raspy_monitor.db 'SELECT username, is_admin FROM users;'` |
| Users not created from DEFAULT_USERS | Verify `.env` format: `username:password:is_admin;user2:pass2:1` (semicolons, no spaces around colons) |
| Governor/fan error: "no new privileges" | Reinstalled service file; should be resolved |
| Governor change fails | Verify: `sudo -l \| grep pi-monitor-gov-control`; check `/etc/sudoers.d/pi-monitor-<user>` exists |
| Fan shows "not detected" | Check: `ls /sys/class/hwmon/hwmon*/pwm1` — Pi 5 fan must be plugged into fan header |
| Fan write fails | Verify scripts: `ls -la /usr/local/bin/pi-monitor-*` (should be root, mode 755) |
| WebSocket disconnect | Check CORS_ORIGINS in `.env` includes your domain; check token hasn't expired |
| Frontend shows 404 | Rebuild: `cd frontend && npm ci && npm run build` |
| Python module errors | Recreate venv: `rm -rf backend/venv && python3 -m venv backend/venv && source backend/venv/bin/activate && pip install -r backend/requirements.txt` |

---

## Updating

```bash
cd ~/pi-monitor
git pull

# If backend deps changed:
cd backend && source venv/bin/activate && pip install -r requirements.txt

# If frontend changed:
cd frontend && npm ci && npm run build

# If database users need to be reset:
setup/init-users.sh

# Restart service:
sudo systemctl restart pi-monitor-k1taru
```

---

## Sharing Your Setup

To share your setup with others:

1. **Share the repo** (GitHub, etc.)
2. **Share your `.env` template** (with secrets removed):
   ```bash
   # In the repo root
   cp backend/.env backend/.env.prod
   # Edit backend/.env.prod to remove SECRET_KEY, JWT_SECRET_KEY
   # Users will copy this as their starting point
   ```
3. **Users clone and run:**
   ```bash
   cd ~/pi-monitor
   sudo setup/setup.sh myusername
   ```

---

## Notes

- **User credentials in `.env`**: Keep `.env` out of git for security. Use `.env.example` as a template.
- **Per-user services**: Multiple users can run independent instances with different settings.
- **SSH into your Pi**: 
  ```bash
  ssh k1taru@raspy.local
  sudo systemctl status pi-monitor-k1taru
  sudo journalctl -u pi-monitor-k1taru -f
  ```
- **Database**: Stored at `~/pi-monitor/backend/raspy_monitor.db` (SQLite3) — inspect with:
  ```bash
  sqlite3 ~/pi-monitor/backend/raspy_monitor.db
  sqlite> SELECT * FROM users;
  sqlite> .quit
  ```


