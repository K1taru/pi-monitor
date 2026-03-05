# Pi Monitor — Setup Guide

Everything you need to get Pi Monitor running on a Raspberry Pi (or any Linux system).

---

## Before You Begin

Make sure these are installed on your Pi:

| Tool | Check | Install if missing |
|---|---|---|
| Python 3.9+ | `python3 --version` | pre-installed on Raspberry Pi OS |
| Node.js + npm | `node --version && npm --version` | `curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |
| Git | `git --version` | `sudo apt-get install -y git` |

---

## Setup (3 steps)

### Step 1 — Clone and configure

```bash
# Clone the repo into your home directory
git clone <your-repo-url> ~/pi-monitor
cd ~/pi-monitor

# Create your .env from the template
cp backend/.env.example backend/.env
nano backend/.env
```

At minimum, set these in `backend/.env`:

```dotenv
SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
PORT=8001
DEFAULT_USERS="yourusername:yourpassword:1"
```

### Step 2 — Run setup

```bash
cd ~/pi-monitor
git pull
sed -i 's/\r$//' setup/setup.sh && chmod +x setup/setup.sh
sudo ./setup/setup.sh k1taru
```

> Replace `k1taru` with your Linux username.

The script automatically:
1. Builds the frontend (`npm install && npm run build`)
2. Creates a Python venv and installs backend dependencies
3. Installs system binaries for fan and governor control
4. Writes a sudoers entry so the service can run privileged commands
5. Creates, enables, and starts a systemd service
6. Initializes the database with users from `.env`

### Step 3 — Verify

```bash
# Check service is running
sudo systemctl status pi-monitor

# Watch live logs
sudo journalctl -u pi-monitor -f

# Verbose ops log (separate from journalctl — tracks every DB/API action)
tail -f ~/pi-monitor/backend/logs/pi-monitor-ops.log

# Open in browser
http://<pi-ip>:8001
```

Login with the credentials you set in `DEFAULT_USERS`.

---

## Useful Commands

```bash
# Service control
sudo systemctl start pi-monitor
sudo systemctl stop pi-monitor
sudo systemctl restart pi-monitor
sudo systemctl status pi-monitor

# Live logs
sudo journalctl -u pi-monitor -f

# Verbose ops log (DB calls, logins, fan/governor changes, metrics)
tail -f ~/pi-monitor/backend/logs/pi-monitor-ops.log

# Check what users are in the database
sqlite3 ~/pi-monitor/backend/monitor.db 'SELECT username, is_admin FROM users;'

# SSH into the Pi
ssh k1taru@raspy.local
```

---

## User Management

**Reinitialize users from `.env`** (safe, won't delete existing users):
```bash
sed -i 's/\r$//' ~/pi-monitor/setup/init-users.sh && chmod +x ~/pi-monitor/setup/init-users.sh
cd ~/pi-monitor && setup/init-users.sh
```

**Wipe and recreate all users from `.env`**:
```bash
sed -i 's/\r$//' ~/pi-monitor/setup/init-users.sh && chmod +x ~/pi-monitor/setup/init-users.sh
cd ~/pi-monitor && setup/init-users.sh --reset
```

**Change password via API:**
```bash
curl -X POST http://localhost:8001/api/auth/change-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"current","new_password":"newpassword"}'
```

---

## Multi-User Setup

Each user shares the same service (`pi-monitor`). Run setup with the Linux user
that should own the process; that user's `.env` will be used.

```bash
sudo ./setup/setup.sh alice
```

If you want genuinely separate instances (different ports, isolated DB), deploy
the repo to separate directories and give each its own `.env` with a different
`PORT`. Then re-run setup for each user.

> Make sure each instance's `backend/.env` has a different `PORT`.

---

## Cloudflared Tunnel (Optional)

If you want to expose the dashboard publicly via a domain:

```bash
# Install (ARM64 for Pi 5)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Authenticate and create a tunnel
cloudflared tunnel login
cloudflared tunnel create pi-monitor

# Create ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /home/<username>/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: your.domain.com
    service: http://localhost:8001
  - service: http_status:404

# Add DNS record and start as a service
cloudflared tunnel route dns pi-monitor your.domain.com
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

---

## Post-Install Checklist

- [ ] Service is running: `sudo systemctl status pi-monitor`
- [ ] Dashboard loads at `http://<pi-ip>:8001`
- [ ] Login works with credentials from `DEFAULT_USERS`
- [ ] Change your password via the Control panel
- [ ] Charts, Terminal, and Controls all work

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found` on setup.sh | Run `sed -i 's/\r$//' setup/setup.sh && chmod +x setup/setup.sh` first (Windows line endings) |
| `npm: command not found` during setup | Install Node.js: `curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |
| Service won't start | `sudo journalctl -u pi-monitor -n 50 --no-pager` |
| Port already in use | `sudo lsof -i :8001`; change `PORT` in `.env` and rerun setup |
| Login fails | Check DB: `sqlite3 backend/monitor.db 'SELECT username, is_admin FROM users;'` |
| Users not created | Re-run: `sed -i 's/\r$//' ~/pi-monitor/setup/init-users.sh && chmod +x ~/pi-monitor/setup/init-users.sh && cd ~/pi-monitor && setup/init-users.sh` |
| Governor/fan control fails | Check: `sudo -l \| grep pi-monitor`; verify `/etc/sudoers.d/pi-monitor` exists |
| Fan not detected | Check: `ls /sys/class/hwmon/hwmon*/pwm1` — Pi 5 fan must be in the fan header |
| Frontend shows 404 | Rebuild: `cd ~/pi-monitor/frontend && npm install && npm run build` |
| Python import errors | Recreate venv: `rm -rf backend/venv && python3 -m venv backend/venv && backend/venv/bin/pip install -r backend/requirements.txt` |
| WebSocket disconnects | Verify `CORS_ORIGINS` in `.env` includes your domain |

---

## Updating

```bash
cd ~/pi-monitor
git pull

# Reinstall backend deps if requirements changed
backend/venv/bin/pip install -r backend/requirements.txt

# Rebuild frontend if UI changed
cd frontend && npm install && npm run build && cd ..

# Restart the service
sudo systemctl restart pi-monitor

# To reset database users from .env (non-destructive)
sed -i 's/\r$//' setup/init-users.sh && chmod +x setup/init-users.sh
setup/init-users.sh

# To wipe and recreate the user database from .env
setup/init-users.sh --reset
```

---

## Sharing With Others

1. Share your repo (push to GitHub, etc.)
2. `.env` is gitignored — share `.env.example` as the template (it has no secrets)
3. Others clone and follow these 3 steps above

```bash
# What someone else runs after cloning:
cp backend/.env.example backend/.env
nano backend/.env   # fill in secrets and users
sed -i 's/\r$//' setup/setup.sh && chmod +x setup/setup.sh
sudo ./setup/setup.sh <their-username>
```


