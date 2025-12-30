#!/bin/bash
#
# Simple Railway Deployment
# Just deploys - set variables in Railway dashboard
#

set -e

echo "🚂 Railway Deployment (Simple)"
echo "================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

echo "🔐 Step 1: Login to Railway"
railway login

echo ""
echo "🎯 Step 2: Link to project"
railway link

echo ""
echo "🚀 Step 3: Deploy"
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "⚠️  IMPORTANT: Set environment variables in Railway dashboard:"
echo "   1. Go to: railway open"
echo "   2. Click 'Variables' tab"
echo "   3. Add these variables:"
echo ""
echo "   SUPABASE_URL=https://jmchmbwhnmlednaycxqh.supabase.co"
echo "   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU"
echo "   ADSPOWER_API_URL=http://local.adspower.net:50325"
echo "   ADSPOWER_PROFILE_IDS=koeuril,koeus69"
echo "   PROXIDIZE_ROTATION_URL=https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"
echo "   PROXYEMPIRE_HOST=mobdedi.proxyempire.io"
echo "   PROXYEMPIRE_PORT=9000"
echo "   PROXYEMPIRE_USERNAME=2ed80b8624"
echo "   PROXYEMPIRE_PASSWORD=570abb9a59"
echo "   OPENAI_API_KEY=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"
echo ""
echo "   4. Click 'Redeploy'"
echo ""
echo "Or copy/paste from: railway_env_vars.txt"
echo ""
echo "📊 View logs: railway logs"
echo "🌐 Open dashboard: railway open"

