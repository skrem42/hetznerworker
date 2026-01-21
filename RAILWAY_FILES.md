# 🚂 Railway Deployment Files

All files created for automated Railway deployment.

## 📁 Files Created

### 1. **railway.json**
Railway configuration file that tells Railway how to build and run your app.

### 2. **Procfile**
Defines what process to run (the crawler).

### 3. **runtime.txt**
Specifies Python 3.13.

### 4. **nixpacks.toml**
Build configuration for installing dependencies.

### 5. **deploy_railway.sh** ⭐
**ONE-COMMAND DEPLOYMENT SCRIPT**

Sets all environment variables and deploys automatically.

### 6. **test_before_deploy.sh**
Pre-deployment test script to catch issues before deploying.

### 7. **RAILWAY_DEPLOY.md**
Complete Railway deployment documentation.

### 8. **QUICKSTART.md**
Quick start guide for both Railway and Mac setup.

---

## 🚀 Deployment Workflow

### Step 1: Test Locally (Optional)
```bash
cd /Users/calummelling/Desktop/redditscraper/hetzner-worker
source venv/bin/activate
./test_before_deploy.sh
```

### Step 2: Deploy to Railway
```bash
./deploy_railway.sh
```

### Step 3: Monitor
```bash
railway logs
```

---

## 📊 What Gets Deployed?

### ✅ Deployed to Railway:
- `crawler_llm.py` - Subreddit discovery and LLM analysis
- `supabase_client.py` - Database operations
- `llm_analyzer.py` - GPT-4 enrichment
- `config.py` - Configuration (reads from env vars)
- `requirements.txt` - Python dependencies

### ❌ NOT Deployed (Mac Only):
- `intel_worker_adspower.py` - Requires AdsPower
- `adspower_client.py` - AdsPower API client
- `monitor.py` - Run locally to monitor both workers

---

## 🔐 Environment Variables

All set automatically by `deploy_railway.sh`:

- ✅ SUPABASE_URL
- ✅ SUPABASE_ANON_KEY
- ✅ ADSPOWER_API_URL (dummy, not used)
- ✅ ADSPOWER_PROFILE_IDS (dummy, not used)
- ✅ PROXIDIZE_ROTATION_URL
- ✅ PROXYEMPIRE_HOST
- ✅ PROXYEMPIRE_PORT
- ✅ PROXYEMPIRE_USERNAME
- ✅ PROXYEMPIRE_PASSWORD
- ✅ OPENAI_API_KEY

---

## 💰 Expected Costs

### Railway (Crawler):
- **Free Tier**: $5/month credit
- **Actual Usage**: ~$3-4/month
- **Result**: Free! 🎉

### Mac (Intel Worker):
- **Cost**: $0 (runs locally)
- **Electricity**: Negligible

---

## 🎯 Complete Architecture

```
┌─────────────────────────────────────────┐
│         RAILWAY (Cloud)                 │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Crawler + LLM Analyzer          │  │
│  │  - Discovers new subs            │  │
│  │  - Enriches with GPT-4           │  │
│  │  - 50-100 subs/hour              │  │
│  │  - $0/month (free tier)          │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
                    ↓
         ┌──────────────────┐
         │    Supabase DB    │
         │  (nsfw_subreddits)│
         └──────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│         YOUR MAC (Local)                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Intel Worker + AdsPower         │  │
│  │  - Scrapes metrics               │  │
│  │  - 150-300 subs/hour             │  │
│  │  - $0/month (local)              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Monitor Dashboard               │  │
│  │  - Real-time stats               │  │
│  │  - Both workers                  │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## ✅ Verification Checklist

After deployment:

- [ ] Railway logs show "Starting subreddit discovery..."
- [ ] No errors in Railway logs
- [ ] New subreddits appearing in Supabase
- [ ] Monitor on Mac shows discovery activity
- [ ] Intel worker on Mac scrapes successfully

---

## 🔄 Update Process

1. Make changes locally
2. Test: `./test_before_deploy.sh`
3. Commit: `git add . && git commit -m "Update"`
4. Push: `git push origin main`
5. Redeploy: `railway up`

Or enable auto-deploy from GitHub in Railway dashboard!

---

**Questions?** See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for detailed guide.





