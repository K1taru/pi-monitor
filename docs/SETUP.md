# Pi Monitor — Manual Setup on Raspberry Pi 5

All commands run on the Pi as user `k1taru`.
Project lives at `/home/k1taru/pi-monitor/`.

---

## Prerequisites

```bash
sudo apt update && sudo apt install -y python3 python3-venv nodejs npm git
```

Verify:

```bash
python3 --version   # 3.11+
node -v             # 18+
```

---

## 1. Clone the repo

```bash
cd ~
git clone <your-repo-url> pi-monitor
cd pi-monitor
```

---

## 2. Backend

### Virtual environment & dependencies

```bash
cd ~/pi-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment file

Create `backend/.env`:

```bash
cat > .env << 'EOF'
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
PORT=8001
CORS_ORIGINS=https://raspy.gymms.space
EOF
```

Or generate the keys manually:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

and paste them into the file:

```dotenv
SECRET_KEY=<paste-here>
JWT_SECRET_KEY=<paste-here>
PORT=8001
CORS_ORIGINS=https://raspy.gymms.space
```

### Quick test

```bash
source venv/bin/activate
python app.py
# Should print "Starting Raspberry Pi Monitor Backend on port 8001..."
# Ctrl+C to stop
```

---

## 3. Frontend

```bash
cd ~/pi-monitor/frontend
```

Create `frontend/.env`:

```bash
echo "VITE_API_URL=https://raspy.gymms.space" > .env
```

Build:

```bash
npm ci
npm run build
```

The output goes to `frontend/dist/` — Flask serves it automatically.

---

## 4. Sudoers (passwordless governor + fan + reboot)

```bash
# Install the fan control wrapper (required for fan PWM writes)
sudo install -m 0755 ~/pi-monitor/deploy/fan-control.sh /usr/local/bin/raspy-fan-control

# Install the CPU governor wrapper (required for governor changes)
sudo install -m 0755 ~/pi-monitor/deploy/gov-control.sh /usr/local/bin/raspy-gov-control

# Install the sudoers drop-in
sudo install -m 0440 ~/pi-monitor/deploy/raspy-monitor-sudoers /etc/sudoers.d/raspy-monitor
sudo visudo -c   # verify no errors
```

This grants `k1taru` passwordless access to:

- `sudo /usr/local/bin/raspy-gov-control` — CPU governor
- `sudo /usr/local/bin/raspy-fan-control` — fan PWM control
- `sudo reboot`

---

## 5. Systemd service

### Install

```bash
sudo cp ~/pi-monitor/deploy/raspy-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspy-monitor
sudo systemctl start raspy-monitor
```

### Verify

```bash
systemctl status raspy-monitor
```

### Useful commands

```bash
# View live logs
journalctl -u raspy-monitor -f

# Restart after code changes
sudo systemctl restart raspy-monitor

# Stop
sudo systemctl stop raspy-monitor
```

---

## 6. Cloudflared tunnel

> Already configured to tunnel `https://raspy.gymms.space` → `localhost:8001`.

If not set up yet:

```bash
# Install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Authenticate & create tunnel
cloudflared tunnel login
cloudflared tunnel create pi-monitor

# Configure  ~/.cloudflared/config.yml
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

## 7. Post-install

1. Open `https://raspy.gymms.space`
2. Login with `admin` / `admin123`
3. **Change the password immediately** (Control panel)
4. Verify all tabs work: Overview, Charts, Processes, Terminal, Control

---

## Updating

```bash
cd ~/pi-monitor
git pull

# If backend deps changed:
cd backend && source venv/bin/activate && pip install -r requirements.txt

# If frontend changed:
cd ~/pi-monitor/frontend && npm ci && npm run build

# Restart service
sudo systemctl restart raspy-monitor
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Service won't start | `journalctl -u raspy-monitor -n 50 --no-pager` |
| Port in use | `sudo lsof -i :8001` |
| Governor/fan error: "no new privileges" | Unit has `NoNewPrivileges=yes` — reinstall with `deploy/raspy-monitor.service` which omits that flag |
| Governor change fails | `sudo -l` — check sudoers is installed; also verify `raspy-gov-control` is installed to `/usr/local/bin/` |
| Fan shows "not detected" | Run `ls /sys/class/hwmon/hwmon*/pwm1` — Pi 5 fan must be plugged into the fan header |
| Fan write fails | Ensure `fan-control.sh` was installed to `/usr/local/bin/raspy-fan-control` with mode 0755 |
| WebSocket disconnect | Check token validity, check CORS_ORIGINS in `.env` |
| Frontend 404 | Rebuild: `cd frontend && npm run build` |
| Python import errors | Activate venv: `source backend/venv/bin/activate` |
