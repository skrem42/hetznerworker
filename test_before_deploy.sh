#!/bin/bash
#
# Pre-deployment Test Script
# Run this before deploying to Railway to catch issues early
#

echo "🧪 Pre-Deployment Tests"
echo "======================="
echo ""

# Check if in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Not in virtual environment. Activating..."
    source venv/bin/activate
fi

# Test 1: Config loads
echo "Test 1: Configuration Loading"
echo "------------------------------"
python3 -c "from config import SUPABASE_URL, PROXYEMPIRE_USERNAME; print('✓ Config loads successfully')" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Check your .env file"
    exit 1
fi
echo ""

# Test 2: Supabase connection
echo "Test 2: Supabase Connection"
echo "----------------------------"
python3 -c "from supabase_client import SupabaseClient; import asyncio; stats = asyncio.run(SupabaseClient().get_queue_stats()); print(f'✓ Connected! Queue has {stats[\"total\"]} subs')" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Check Supabase credentials"
    exit 1
fi
echo ""

# Test 3: Proxy connection
echo "Test 3: Proxy Connection"
echo "------------------------"
python3 << 'EOF'
import asyncio
import httpx
from config import CRAWLER_PROXY

async def test():
    try:
        async with httpx.AsyncClient(proxy=CRAWLER_PROXY, timeout=10.0, verify=False) as client:
            response = await client.get("https://api.ipify.org?format=json")
            data = response.json()
            print(f"✓ Proxy works! Exit IP: {data['ip']}")
            return True
    except Exception as e:
        print(f"✗ Proxy failed: {e}")
        return False

result = asyncio.run(test())
exit(0 if result else 1)
EOF
if [ $? -eq 0 ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Check proxy credentials"
    exit 1
fi
echo ""

# Test 4: Reddit API access
echo "Test 4: Reddit API Access (via proxy)"
echo "--------------------------------------"
python3 << 'EOF'
import asyncio
import httpx
from config import CRAWLER_PROXY

async def test():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        async with httpx.AsyncClient(proxy=CRAWLER_PROXY, timeout=10.0, verify=False, follow_redirects=True) as client:
            response = await client.get("https://www.reddit.com/r/python/about.json", headers=headers)
            if response.status_code == 200:
                data = response.json()
                subs = data.get("data", {}).get("subscribers", 0)
                print(f"✓ Reddit API works! r/python has {subs:,} subscribers")
                return True
            else:
                print(f"✗ Reddit API returned {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Reddit API failed: {e}")
        return False

result = asyncio.run(test())
exit(0 if result else 1)
EOF
if [ $? -eq 0 ]; then
    echo "✅ PASS"
else
    echo "⚠️  WARN - Reddit might be blocking this IP (try rotating)"
fi
echo ""

# Test 5: OpenAI API
echo "Test 5: OpenAI API"
echo "------------------"
python3 << 'EOF'
from openai import OpenAI
from config import OPENAI_API_KEY

try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Just verify the key format, don't make actual API call
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        print("✓ OpenAI API key format looks valid")
        exit(0)
    else:
        print("✗ OpenAI API key invalid")
        exit(1)
except Exception as e:
    print(f"✗ OpenAI check failed: {e}")
    exit(1)
EOF
if [ $? -eq 0 ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Check OpenAI API key"
    exit 1
fi
echo ""

echo "======================================"
echo "🎉 All tests passed!"
echo "======================================"
echo ""
echo "✅ Ready to deploy to Railway!"
echo ""
echo "Run: ./deploy_railway.sh"
echo ""





