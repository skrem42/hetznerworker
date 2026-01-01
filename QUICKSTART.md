# ⚡ Quick Start Guide

Get your Reddit scraper running in 5 minutes!

## 🎯 Recommended Setup

### ☁️ Crawler on Railway (24/7 Discovery)
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
./deploy_railway.sh
```

### 💻 Intel Worker on Mac (Metric Scraping)
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
source venv/bin/activate
python intel_worker_adspower.py
```

## 📊 Monitor Everything

### On Railway:
```bash
railway logs
```

### On Mac:
```bash
python monitor.py
```

---

## 📖 Detailed Guides

- **Railway Deployment**: See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)
- **Hetzner Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Full Documentation**: See [README.md](README.md)

---

## 🔥 That's It!

Your scraper is now:
- ✅ Discovering new NSFW subreddits 24/7 (Railway)
- ✅ Scraping detailed metrics with AdsPower (Mac)
- ✅ Enriching data with GPT-4 analysis (Railway)
- ✅ Storing everything in Supabase

**View your data**: https://jmchmbwhnmlednaycxqh.supabase.co

🎉 Happy scraping!



