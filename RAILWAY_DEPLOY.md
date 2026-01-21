# 🚂 Railway Deployment Guide (Crawler Only)

Deploy just the crawler to Railway - no browsers, no AdsPower needed!

## ✅ Why Railway for the Crawler?

- ✅ **Residential IP range** - Not flagged by Reddit like Hetzner datacenter IPs
- ✅ **24/7 uptime** - Auto-restarts on crashes
- ✅ **Easy logs** - Real-time monitoring in dashboard
- ✅ **Free tier available** - $5/month credit
- ✅ **No browser needed** - Just JSON API calls

## 🚀 One-Command Deployment

```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
./deploy_railway.sh
```

That's it! The script will:
1. ✅ Install Railway CLI (if needed)
2. ✅ Login to Railway
3. ✅ Create/link project
4. ✅ Set all environment variables
5. ✅ Deploy the crawler
6. ✅ Show you the logs

## 📊 Monitor Your Deployment

### View Live Logs
```bash
railway logs
```

### Check Status
```bash
railway status
```

### Open Dashboard
```bash
railway open
```

### View Environment Variables
```bash
railway variables
```

## 🔧 Manual Deployment (Alternative)

If the script fails, deploy manually:

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login
```bash
railway login
```

### 3. Create Project
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
railway init
```

### 4. Set Environment Variables

Either use the Railway dashboard (easier) or CLI:

```bash
# Supabase
railway variables set SUPABASE_URL="https://jmchmbwhnmlednaycxqh.supabase.co"
railway variables set SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU"

# AdsPower (dummy - required by config but not used)
railway variables set ADSPOWER_API_URL="http://local.adspower.net:50325"
railway variables set ADSPOWER_PROFILE_IDS="koeuril,koeus69"

# Proxies
railway variables set PROXIDIZE_ROTATION_URL="https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"
railway variables set PROXYEMPIRE_HOST="mobdedi.proxyempire.io"
railway variables set PROXYEMPIRE_PORT="9000"
railway variables set PROXYEMPIRE_USERNAME="2ed80b8624"
railway variables set PROXYEMPIRE_PASSWORD="570abb9a59"

# OpenAI
railway variables set OPENAI_API_KEY="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"
```

### 5. Deploy
```bash
railway up
```

## 🎯 Complete Setup (Crawler + Intel Worker)

### ☁️ On Railway (24/7):
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
./deploy_railway.sh
```
- ✅ Runs `crawler_llm.py`
- ✅ Discovers new subreddits
- ✅ Enriches with LLM analysis

### 💻 On Your Mac (when you want):
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
source venv/bin/activate
python intel_worker_adspower.py
```
- ✅ Uses AdsPower browsers
- ✅ Scrapes subreddit metrics
- ✅ Works with your existing setup

## 📈 Expected Performance

### Crawler on Railway:
- **Discovery Rate**: 50-100 new subs/hour
- **Cost**: ~$5/month (within free tier)
- **Uptime**: 99.9%

### Intel Worker on Mac:
- **Scraping Rate**: 150-300 subs/hour (with 2 browsers)
- **Cost**: $0 (runs locally)
- **Run**: Whenever you want

## 🐛 Troubleshooting

### Build Fails
```bash
# Check logs
railway logs --build

# Common fix: Clear build cache
railway run --detach
```

### Still Getting 403s
```bash
# SSH into Railway container and test
railway shell

# Run proxy test
python test_proxy.py
```

### Environment Variables Not Loading
```bash
# List all variables
railway variables

# Make sure all required vars are set
railway variables set KEY="value"
```

### Deployment Hangs
```bash
# Cancel and retry
Ctrl+C
railway up
```

## 💰 Railway Pricing

- **Free Tier**: $5 credit/month (enough for crawler)
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

Your crawler should stay within the free tier! 🎉

## 🔄 Update Deployment

After making code changes:

```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker

# Commit changes
git add .
git commit -m "Update crawler"
git push origin main

# Redeploy to Railway
railway up
```

Or enable auto-deploy from GitHub in Railway dashboard!

## 📞 Support

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway

---

**Ready to deploy?** Run `./deploy_railway.sh` and you're done! 🚀





