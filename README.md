# Hetzner Worker Setup

**Two-script solution for 24/7 Reddit subreddit intelligence scraping**

## Overview

This setup consists of two independent workers that run simultaneously:

1. **Intel Worker** (`intel_worker_adspower.py`) - Scrapes subreddit metrics using AdsPower browsers with ProxyEmpire
2. **Crawler + LLM** (`crawler_llm.py`) - Discovers new subreddits and enriches with LLM analysis using SOAX proxies

## Architecture

```
┌─────────────────────────────────────────┐
│         Hetzner VPS                     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Script 1: Intel Worker         │   │
│  │  - AdsPower (10 browsers)       │   │
│  │  - ProxyEmpire mobile proxy     │   │
│  │  - ~1,800 subs/hour             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Script 2: Crawler + LLM        │   │
│  │  - SOAX proxy rotation          │   │
│  │  - JSON API discovery           │   │
│  │  - GPT-4o-mini analysis         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Monitor Dashboard              │   │
│  │  - Real-time stats              │   │
│  │  - Browser health               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Prerequisites

- Hetzner VPS (or any Ubuntu/Debian server)
- AdsPower installed and configured
- 10 Reddit accounts
- ProxyEmpire mobile proxy subscription
- SOAX proxy subscription
- OpenAI API key
- Supabase project

## Quick Start

### 1. Initial Setup on Hetzner

```bash
# SSH into your Hetzner VPS
ssh root@your-server-ip

# Clone your repository
cd /root
git clone https://github.com/your-username/redditscraper.git
cd redditscraper/hetzner-worker

# Create .env file from example
cp env.example .env
nano .env  # Edit with your credentials

# Run setup script
chmod +x setup.sh
sudo ./setup.sh
```

**Important**: Fill in your `.env` file with real credentials before running setup!

### 2. Configure AdsPower

AdsPower must run on a machine with a desktop environment (Windows, Mac, or Linux with GUI).

#### Option A: Install AdsPower on Hetzner with RDP

```bash
# Install XFCE desktop and RDP server
sudo apt install -y xfce4 xrdp
sudo systemctl enable xrdp
sudo systemctl start xrdp

# Set root password for RDP login
sudo passwd root

# Connect via RDP from your local machine
# Windows: Remote Desktop Connection
# Mac: Microsoft Remote Desktop
# Linux: Remmina

# Inside RDP session, download and install AdsPower:
# https://www.adspower.net/download
```

#### Option B: Run AdsPower Locally (Recommended for Testing)

1. Install AdsPower on your local Windows/Mac
2. Configure SSH tunnel to forward AdsPower API:

```bash
# On your local machine, forward AdsPower API port
ssh -L 50325:localhost:50325 root@your-server-ip

# Keep this terminal open while workers run
```

### 3. Create Browser Profiles in AdsPower

1. Open AdsPower
2. Click "New Profile" 10 times to create 10 profiles
3. For each profile:
   - **Name**: `Reddit_Account_1`, `Reddit_Account_2`, etc.
   - **Proxy Type**: HTTP
   - **Proxy Host**: `mobdedi.proxyempire.io`
   - **Proxy Port**: `9000`
   - **Username**: `2ed80b8624`
   - **Password**: `570abb9a59`
   - **Fingerprint**: Generate Random
   - **User Agent**: Auto (AdsPower handles this)

4. Login to Reddit in each browser:
   - Click "Open" for each profile
   - Navigate to `reddit.com`
   - Login with your Reddit account credentials
   - Cookies are automatically saved by AdsPower

### 4. Get Profile IDs

1. In AdsPower, right-click each profile → "Copy User ID"
2. Update `.env` file:

```bash
# Example with 2 profiles (add more comma-separated)
ADSPOWER_PROFILE_IDS=j1x9k2m3,k2y8l3n4,l3z7m4o5
```

### 5. Enable AdsPower API

1. AdsPower → Settings → API Settings
2. Enable "Local API"
3. Port should be `50325` (default)
4. Click "Save"

### 6. Test AdsPower Connection

```bash
cd /root/hetzner-worker
source venv/bin/activate
python adspower_client.py
```

You should see:
```
✓ AdsPower API connected successfully
✓ Found 10 profiles:
  - Reddit_Account_1 (ID: j1x9k2m3)
  - Reddit_Account_2 (ID: k2y8l3n4)
  ...
```

### 7. Configure Credentials

Edit `config.py` and update:

```python
# OpenAI API Key
OPENAI_API_KEY = "sk-your-actual-key-here"

# AdsPower Profile IDs (from step 4)
ADSPOWER_PROFILE_IDS = [
    "your_profile_id_1",
    "your_profile_id_2",
    # ... 10 total
]
```

ProxyEmpire and SOAX credentials are already configured.

### 8. Start Workers

**Option A: Manual Start (for testing)**

```bash
# Terminal 1: Intel Worker
./start_intel_worker.sh

# Terminal 2: Crawler + LLM
./start_crawler.sh

# Terminal 3: Monitor
python monitor.py
```

**Option B: Systemd Services (for production)**

```bash
# Start services
sudo systemctl start intel-worker
sudo systemctl start crawler-llm

# Enable auto-start on boot
sudo systemctl enable intel-worker
sudo systemctl enable crawler-llm

# Check status
sudo systemctl status intel-worker
sudo systemctl status crawler-llm

# View logs
sudo journalctl -u intel-worker -f
sudo journalctl -u crawler-llm -f
```

## Configuration

### `config.py`

All configuration is centralized in `config.py`:

```python
# Worker Settings
INTEL_BATCH_SIZE = 20          # Subs per batch (intel worker)
INTEL_TIMEOUT_SECONDS = 30     # Timeout per subreddit
INTEL_CONCURRENT = 10          # Match number of browsers
INTEL_RETRY_MAX = 5            # Max retries before marking failed

CRAWLER_BATCH_SIZE = 50        # Subs per batch (crawler)
CRAWLER_TIMEOUT_SECONDS = 15   # Timeout per request
CRAWLER_RETRY_MAX = 5          # Max retries per endpoint
CRAWLER_MIN_SUBSCRIBERS = 5000 # Minimum subs to discover

LLM_BATCH_SIZE = 10            # Subs to analyze per batch
LLM_INTERVAL_SECONDS = 600     # Run LLM every 10 minutes
LLM_MAX_CONCURRENT = 5         # Concurrent LLM requests
```

### Proxy Configuration

**ProxyEmpire (Intel Worker)**:
- Configured in AdsPower profiles
- Rotation URL available for manual IP rotation if needed

**SOAX (Crawler)**:
- 5 rotating proxy sessions
- Automatic rotation on 403/429 errors
- Session length: 5 minutes

## Monitoring

### Real-Time Dashboard

```bash
python monitor.py
```

Shows:
- Active browsers (10/10)
- Queue status (pending/completed)
- Intel table stats
- LLM analysis progress
- Success rates

### Log Files

```bash
# Intel worker logs
tail -f logs/intel_worker.log

# Crawler + LLM logs
tail -f logs/crawler_llm.log

# Systemd logs
sudo journalctl -u intel-worker -f
sudo journalctl -u crawler-llm -f
```

## Troubleshooting

### AdsPower API Not Responding

**Error**: `Failed to connect to AdsPower API`

**Solutions**:
1. Check AdsPower is running
2. Verify API is enabled (Settings → API Settings)
3. Check port 50325 is accessible
4. If using SSH tunnel, ensure tunnel is active

**Test**:
```bash
curl http://local.adspower.net:50325/api/v1/user/list
```

### Browsers Not Starting

**Error**: `Failed to start profile {profile_id}`

**Solutions**:
1. Verify profile ID is correct (copy from AdsPower UI)
2. Check profile isn't already open
3. Close browser manually in AdsPower and retry
4. Restart AdsPower application

### SOAX Proxies Failing

**Error**: High failure rate on crawler

**Solutions**:
1. Verify SOAX subscription is active
2. Check session IDs in `config.py` are unique
3. Increase `CRAWLER_RETRY_MAX` if needed
4. Reduce `CRAWLER_BATCH_SIZE` to slow down requests

### OpenAI API Errors

**Error**: `OPENAI_API_KEY is required`

**Solutions**:
1. Set in `config.py` or environment variable
2. Verify API key is valid
3. Check OpenAI account has credits

**Test**:
```bash
export OPENAI_API_KEY="sk-your-key"
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### Database Connection Issues

**Error**: `SUPABASE_URL and SUPABASE_ANON_KEY must be set`

**Solutions**:
1. Verify Supabase credentials in `config.py`
2. Check network connectivity
3. Verify Supabase project is active

**Test**:
```bash
python -c "from supabase_client import SupabaseClient; print(SupabaseClient())"
```

## Performance Optimization

### Expected Throughput

- **Intel Worker**: 1,800 subs/hour (10 browsers × 3 subs/min)
- **Crawler**: 6,000 subs/hour (discovery only)
- **LLM**: 60 subs/hour (enrichment)

### Scaling Up

**More Browsers**:
1. Create more Reddit accounts
2. Add more profiles in AdsPower
3. Update `ADSPOWER_PROFILE_IDS` in config
4. Increase `INTEL_CONCURRENT` to match

**Faster LLM**:
1. Increase `LLM_MAX_CONCURRENT` (be careful with rate limits)
2. Decrease `LLM_INTERVAL_SECONDS` for more frequent runs

**More Discovery**:
1. Increase `CRAWLER_BATCH_SIZE`
2. Add more SOAX proxy sessions

## Maintenance

### Daily Tasks

```bash
# Check worker status
sudo systemctl status intel-worker crawler-llm

# Check logs for errors
grep ERROR logs/*.log

# Monitor dashboard
python monitor.py
```

### Weekly Tasks

```bash
# Restart workers (clears memory)
sudo systemctl restart intel-worker crawler-llm

# Check disk space
df -h

# Rotate logs (if not using logrotate)
mv logs/intel_worker.log logs/intel_worker.log.old
mv logs/crawler_llm.log logs/crawler_llm.log.old
```

### Monthly Tasks

```bash
# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Check for Reddit account suspensions
# Login to each account manually in AdsPower

# Verify proxy subscriptions are active
# ProxyEmpire: https://panel.proxyempire.io
# SOAX: https://soax.com/dashboard
```

## Security Notes

1. **Never commit `config.py` with real credentials**
2. Keep AdsPower profiles secure (contains Reddit cookies)
3. Use SSH keys for Hetzner access, not passwords
4. Regularly rotate Reddit account passwords
5. Monitor proxy usage to avoid unexpected charges

## Support

### Checking System Health

```bash
# Test AdsPower connection
python adspower_client.py

# Test database connection
python -c "from supabase_client import SupabaseClient; s = SupabaseClient(); print('Connected')"

# Test LLM
python -c "from llm_analyzer import SubredditLLMAnalyzer; print('LLM OK')"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Browsers crash | Restart AdsPower, check memory usage |
| High failure rate | Rotate proxies, check Reddit isn't blocking IPs |
| Slow performance | Check CPU usage, increase delays between requests |
| Database errors | Check Supabase connection, verify schema is correct |

## File Structure

```
hetzner-worker/
├── config.py                    # Configuration (UPDATE THIS)
├── adspower_client.py           # AdsPower API wrapper
├── intel_worker_adspower.py     # Script 1: Intel worker
├── crawler_llm.py               # Script 2: Crawler + LLM
├── supabase_client.py           # Database client
├── llm_analyzer.py              # LLM analyzer
├── monitor.py                   # Monitoring dashboard
├── setup.sh                     # Automated setup script
├── start_intel_worker.sh        # Launch script 1
├── start_crawler.sh             # Launch script 2
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── logs/                        # Log files
│   ├── intel_worker.log
│   └── crawler_llm.log
└── systemd/                     # Systemd service files
    ├── intel-worker.service
    └── crawler-llm.service
```

## License

MIT License - Use freely for your projects.

## Credits

Built for efficient 24/7 Reddit NSFW subreddit intelligence scraping.

