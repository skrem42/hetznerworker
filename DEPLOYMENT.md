# 🚀 Hetzner Deployment Guide

Complete step-by-step guide to deploy your Reddit scraper on a Hetzner VPS.

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Hetzner VPS (Ubuntu 22.04 or later)
- ✅ GitHub repository with your code
- ✅ Supabase project with credentials
- ✅ ProxyEmpire mobile proxy subscription
- ✅ Proxidize proxy token
- ✅ OpenAI API key
- ✅ AdsPower installed (local machine or VPS with GUI)

## 🔐 Step 1: Prepare Your Local Repository

### 1.1 Create .env File

```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker

# Rename env.txt to .env
mv env.txt .env

# Verify .gitignore includes .env
cat .gitignore | grep ".env"
```

### 1.2 Test Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Test configuration loads correctly
python -c "from config import SUPABASE_URL; print('Config OK:', SUPABASE_URL)"

# Run quick test
python monitor.py
```

### 1.3 Commit and Push to GitHub

```bash
# Add all files (except .env which is gitignored)
git add .
git commit -m "Add environment variable configuration"
git push origin main
```

**⚠️ Important**: Verify `.env` is NOT in your git repo:
```bash
git status  # Should NOT show .env as tracked
```

## 🖥️ Step 2: Server Setup

### 2.1 SSH into Hetzner

```bash
ssh root@your-server-ip
```

### 2.2 Update System

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget
```

### 2.3 Clone Repository

```bash
cd /root
git clone https://github.com/YOUR_USERNAME/redditscraper.git
cd redditscraper/hetzner-worker
```

## 🔑 Step 3: Configure Environment

### 3.1 Create .env File on Server

```bash
# Copy example
cp env.example .env

# Edit with your credentials
nano .env
```

Paste your actual values:

```bash
# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL=
SUPABASE_ANON_KEY=your-actual-key-here

# =============================================================================
# ADSPOWER CONFIGURATION
# =============================================================================
ADSPOWER_API_URL=http://local.adspower.net:50325
ADSPOWER_PROFILE_IDS=koeuril,koeus69

# =============================================================================
# PROXY CONFIGURATION
# =============================================================================
PROXIDIZE_ROTATION_URL=https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/YOUR_TOKEN/
PROXYEMPIRE_HOST=mobdedi.proxyempire.io
PROXYEMPIRE_PORT=9000
PROXYEMPIRE_USERNAME=your_username
PROXYEMPIRE_PASSWORD=your_password

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY=sk-proj-your-key-here
```

Save and exit (Ctrl+X, then Y, then Enter).

## 📦 Step 4: Install Dependencies

```bash
# Run automated setup
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Install Playwright browsers
- ✅ Create systemd services
- ✅ Set up logs directory

## 🤖 Step 5: Configure AdsPower

### Option A: AdsPower on Local Machine (Recommended)

If running AdsPower on your Mac/Windows:

1. **On your local machine**, verify AdsPower API is accessible:
```bash
curl http://localhost:50325/api/v1/browser/list-browser
```

2. **Create SSH tunnel** from server to local AdsPower:
```bash
# On your local machine
ssh -R 50325:localhost:50325 root@your-server-ip

# Keep this terminal open while workers run
```

3. **On the server**, update `.env`:
```bash
ADSPOWER_API_URL=http://localhost:50325
```

### Option B: AdsPower on Hetzner (Advanced)

If you want to run everything on Hetzner:

```bash
# Install desktop environment
apt install -y xfce4 xrdp
systemctl enable xrdp
systemctl start xrdp

# Set password for RDP access
passwd root

# Connect via RDP client to install AdsPower
# Then follow AdsPower setup in README.md
```

## ✅ Step 6: Test Configuration

### 6.1 Test Database Connection

```bash
cd /root/redditscraper/hetzner-worker
source venv/bin/activate
python -c "from supabase_client import SupabaseClient; import asyncio; asyncio.run(SupabaseClient().get_queue_stats())"
```

### 6.2 Test AdsPower Connection

```bash
python -c "from adspower_client import AdsPowerClient; import asyncio; print(asyncio.run(AdsPowerClient().list_profiles()))"
```

### 6.3 Test Proxy

```bash
python -c "import httpx; print(httpx.get('https://api.ipify.org', proxies={'http': 'http://YOUR_PROXY_URL'}).text)"
```

## 🚀 Step 7: Start Services

### 7.1 Start Crawler Only (Recommended)

```bash
# Start crawler (discovers new subs)
systemctl start hetzner-crawler
systemctl enable hetzner-crawler

# Check status
systemctl status hetzner-crawler

# View logs
journalctl -u hetzner-crawler -f
```

### 7.2 Start Intel Worker (If AdsPower Ready)

```bash
# Start intel worker (scrapes metrics)
systemctl start hetzner-intel-worker
systemctl enable hetzner-intel-worker

# Check status
systemctl status hetzner-intel-worker

# View logs
journalctl -u hetzner-intel-worker -f
```

## 📊 Step 8: Monitor Progress

### 8.1 Real-time Dashboard

```bash
cd /root/redditscraper/hetzner-worker
source venv/bin/activate
python monitor.py
```

### 8.2 View Logs

```bash
# Crawler logs
tail -f logs/crawler_llm.log

# Intel worker logs
tail -f logs/intel_worker.log

# System logs
journalctl -u hetzner-crawler -f
journalctl -u hetzner-intel-worker -f
```

## 🔧 Management Commands

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

### Update Code

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

## 🐛 Troubleshooting

### Issue: "Module not found" errors

```bash
cd /root/redditscraper/hetzner-worker
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: AdsPower connection failed

```bash
# Check if tunnel is active (if using local AdsPower)
netstat -an | grep 50325

# Test API directly
curl http://localhost:50325/api/v1/browser/list-browser
```

### Issue: Proxy errors

```bash
# Test proxy connectivity
curl -x http://USERNAME:PASSWORD@mobdedi.proxyempire.io:9000 https://api.ipify.org
```

### Issue: Database connection failed

```bash
# Verify .env has correct credentials
cat .env | grep SUPABASE

# Test connection
python -c "from config import SUPABASE_URL; print(SUPABASE_URL)"
```

## 📈 Performance Optimization

### Increase Browser Count

1. Create more AdsPower profiles
2. Update `.env`:
```bash
ADSPOWER_PROFILE_IDS=profile1,profile2,profile3,profile4,profile5
```
3. Update `config.py`:
```python
INTEL_CONCURRENT = 5  # Match number of profiles
INTEL_BATCH_SIZE = 15  # 3x browser count
```

### Adjust Timeouts

Edit `config.py`:
```python
INTEL_TIMEOUT_SECONDS = 120  # Reduce if pages load faster
CRAWLER_BATCH_SIZE = 100     # Increase for faster discovery
```

## 🔒 Security Best Practices

1. **Never commit `.env`** - Always in `.gitignore`
2. **Rotate credentials** regularly
3. **Use SSH keys** instead of passwords
4. **Enable firewall**:
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

## 🎯 Recommended Setup

For optimal 24/7 operation:

### **On Hetzner (Cloud Server):**
- ✅ Crawler - Discovers new subreddits
- ✅ LLM Analyzer - Enriches data
- ✅ Monitor dashboard

### **On Local Machine (Mac/Windows):**
- ✅ AdsPower with browsers - Scrapes metrics
- ✅ Intel worker - Connects to AdsPower

This splits the workload optimally:
- Hetzner handles discovery (no GUI needed)
- Local machine handles browser scraping (needs GUI)

## 📞 Support

If you encounter issues:
1. Check logs: `journalctl -u hetzner-crawler -f`
2. Test components individually
3. Verify `.env` has all required values
4. Ensure services are running: `systemctl status hetzner-crawler`

---

**Ready to deploy!** 🚀 Start with just the crawler, then add the intel worker once AdsPower is configured.



