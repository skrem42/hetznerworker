#!/bin/bash
#
# Automated Railway Deployment Script
# Sets all environment variables and deploys the crawler
#

set -e  # Exit on error

echo "🚂 Railway Deployment Script"
echo "=============================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

echo "🔐 Logging into Railway..."
railway login

echo ""
echo "🎯 Creating/Linking Railway project..."
railway init

echo ""
echo "⚙️  Setting environment variables..."

# Use the correct Railway CLI v3 syntax
railway variables --set SUPABASE_URL="https://jmchmbwhnmlednaycxqh.supabase.co"
railway variables --set SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU"
railway variables --set ADSPOWER_API_URL="http://local.adspower.net:50325"
railway variables --set ADSPOWER_PROFILE_IDS="koeuril,koeus69"
railway variables --set PROXIDIZE_ROTATION_URL="https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"
railway variables --set PROXYEMPIRE_HOST="mobdedi.proxyempire.io"
railway variables --set PROXYEMPIRE_PORT="9000"
railway variables --set PROXYEMPIRE_USERNAME="2ed80b8624"
railway variables --set PROXYEMPIRE_PASSWORD="570abb9a59"
railway variables --set OPENAI_API_KEY="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"

echo "✓ Environment variables set!"
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Useful commands:"
echo "  railway logs          - View live logs"
echo "  railway status        - Check deployment status"
echo "  railway open          - Open Railway dashboard"
echo "  railway variables     - View all variables"
echo ""
echo "🎉 Your crawler is now running on Railway!"

