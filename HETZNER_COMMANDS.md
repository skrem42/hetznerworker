# 🚀 Quick Hetzner Deployment Commands

Copy and paste these commands to deploy on your Hetzner server.

## 📥 Step 1: Clone Repository

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget

# Clone your repo
cd /root
git clone https://github.com/YOUR_USERNAME/redditscraper.git
cd redditscraper/hetzner-worker
```

## 🔑 Step 2: Create .env File

```bash
# Create .env from example
cp env.example .env

# Edit with your credentials
nano .env
```

**Paste your actual credentials** (from your local `env.txt`):

```bash
SUPABASE_URL=https://jmchmbwhnmlednaycxqh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU

ADSPOWER_API_URL=http://local.adspower.net:50325
ADSPOWER_PROFILE_IDS=koeuril,koeus69

PROXIDIZE_ROTATION_URL=https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/

PROXYEMPIRE_HOST=mobdedi.proxyempire.io
PROXYEMPIRE_PORT=9000
PROXYEMPIRE_USERNAME=2ed80b8624
PROXYEMPIRE_PASSWORD=570abb9a59

OPENAI_API_KEY=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
```

Save: `Ctrl+X`, then `Y`, then `Enter`

## 📦 Step 3: Run Setup

```bash
# Make setup executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

## ✅ Step 4: Test Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Test config loads
python -c "from config import SUPABASE_URL; print('✓ Config OK')"

# Test database connection
python -c "from supabase_client import SupabaseClient; import asyncio; print('Queue stats:', asyncio.run(SupabaseClient().get_queue_stats()))"
```

## 🚀 Step 5: Start Services

### Option A: Start Crawler Only (Recommended for Cloud)

```bash
# Start crawler service
systemctl start hetzner-crawler
systemctl enable hetzner-crawler

# Check status
systemctl status hetzner-crawler

# View logs
journalctl -u hetzner-crawler -f
```

### Option B: Start Both Services (If AdsPower is Ready)

```bash
# Start both services
systemctl start hetzner-crawler
systemctl start hetzner-intel-worker
systemctl enable hetzner-crawler
systemctl enable hetzner-intel-worker

# Check status
systemctl status hetzner-crawler
systemctl status hetzner-intel-worker
```

## 📊 Step 6: Monitor

```bash
# Run real-time dashboard
cd /root/redditscraper/hetzner-worker
source venv/bin/activate
python monitor.py
```

## 🔧 Common Commands

### View Logs

```bash
# Live crawler logs
journalctl -u hetzner-crawler -f

# Live intel worker logs
journalctl -u hetzner-intel-worker -f

# File logs
tail -f /root/redditscraper/hetzner-worker/logs/crawler_llm.log
tail -f /root/redditscraper/hetzner-worker/logs/intel_worker.log
```

### Restart Services

```bash
systemctl restart hetzner-crawler
systemctl restart hetzner-intel-worker
```

### Stop Services

```bash
systemctl stop hetzner-crawler
systemctl stop hetzner-intel-worker
```

### Update from Git

```bash
cd /root/redditscraper
git pull origin main
systemctl restart hetzner-crawler
systemctl restart hetzner-intel-worker
```

### Check Service Status

```bash
systemctl status hetzner-crawler
systemctl status hetzner-intel-worker
```

## 🤖 AdsPower Setup (If Running Intel Worker)

### If AdsPower is on Your Local Machine:

**On your local machine:**
```bash
# Create SSH tunnel to forward AdsPower API
ssh -R 50325:localhost:50325 root@your-server-ip

# Keep this terminal open while workers run
```

**On the server (.env):**
```bash
ADSPOWER_API_URL=http://localhost:50325
```

### If AdsPower is on Hetzner:

```bash
# Install desktop environment
apt install -y xfce4 xrdp
systemctl enable xrdp
systemctl start xrdp
passwd root

# Connect via RDP and install AdsPower
# Then configure profiles as per README.md
```

## 🐛 Troubleshooting

### Fix "Module not found"

```bash
cd /root/redditscraper/hetzner-worker
source venv/bin/activate
pip install -r requirements.txt
```

### Test Proxy

```bash
curl -x http://2ed80b8624:570abb9a59@mobdedi.proxyempire.io:9000 https://api.ipify.org
```

### Test AdsPower Connection

```bash
curl http://localhost:50325/api/v1/browser/list-browser
```

## 📈 Performance Monitoring

```bash
# Check service resource usage
systemctl status hetzner-crawler
systemctl status hetzner-intel-worker

# Check system resources
htop

# Check disk space
df -h

# Check memory
free -h
```

---

**That's it!** Your scraper should now be running 24/7 on Hetzner. 🎉

Monitor with `python monitor.py` to see real-time stats!




