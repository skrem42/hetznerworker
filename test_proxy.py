#!/usr/bin/env python3
"""
Test proxy connection on Hetzner
Run this to diagnose 403 issues
"""
import asyncio
import httpx
from config import PROXYEMPIRE_URL, CRAWLER_PROXY

async def test_proxy():
    """Test if proxy is working correctly"""
    
    print("="*80)
    print("PROXY CONNECTION TEST")
    print("="*80)
    print(f"Proxy URL: {CRAWLER_PROXY[:50]}..." if len(CRAWLER_PROXY) > 50 else f"Proxy URL: {CRAWLER_PROXY}")
    print()
    
    # Test 1: Check actual IP without proxy
    print("Test 1: Without Proxy (should be Hetzner datacenter IP)")
    print("-"*80)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.ipify.org?format=json")
            data = response.json()
            print(f"✓ Your IP without proxy: {data['ip']}")
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 2: Check IP with proxy
    print("Test 2: With Proxy (should be mobile residential IP)")
    print("-"*80)
    try:
        async with httpx.AsyncClient(
            proxy=CRAWLER_PROXY,
            timeout=10.0,
            verify=False
        ) as client:
            response = await client.get("https://api.ipify.org?format=json")
            data = response.json()
            print(f"✓ Your IP with proxy: {data['ip']}")
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Proxy connection failed: {e}")
        print(f"  This is why you're getting 403s!")
    print()
    
    # Test 3: Reddit JSON endpoint without proxy
    print("Test 3: Reddit API without proxy (will likely 403)")
    print("-"*80)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://www.reddit.com/r/python/about.json")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✓ Reddit allows your IP!")
            else:
                print(f"✗ Reddit blocks your IP (datacenter detected)")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 4: Reddit JSON endpoint with proxy
    print("Test 4: Reddit API with proxy (should work)")
    print("-"*80)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient(
            proxy=CRAWLER_PROXY,
            timeout=10.0,
            verify=False,
            follow_redirects=True
        ) as client:
            response = await client.get(
                "https://www.reddit.com/r/python/about.json",
                headers=headers
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                subscribers = data.get("data", {}).get("subscribers", 0)
                print(f"✓ SUCCESS! Reddit API works with proxy")
                print(f"  r/python has {subscribers:,} subscribers")
            elif response.status_code == 403:
                print(f"✗ STILL 403 - Proxy not working correctly")
                print(f"  Check your ProxyEmpire credentials in .env")
            else:
                print(f"✗ HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"  Proxy connection failed!")
    print()
    
    print("="*80)
    print("DIAGNOSIS")
    print("="*80)
    print("If Test 4 shows 403:")
    print("  → Proxy is NOT being used (check .env file)")
    print("  → Or proxy credentials are wrong")
    print()
    print("If Test 4 shows 200:")
    print("  → Proxy works! Check crawler code for issues")
    print()
    print("If Test 2 fails:")
    print("  → Proxy credentials invalid or proxy is down")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_proxy())





