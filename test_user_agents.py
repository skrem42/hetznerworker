#!/usr/bin/env python3
"""
Test User Agent Rotation
Verify that random user agents and realistic headers work with Reddit API
"""
import asyncio
import httpx
from user_agents import get_random_user_agent, get_reddit_headers, get_reddit_cookies
from config import CRAWLER_PROXY

async def test_user_agents():
    """Test user agent rotation with Reddit API."""
    
    print("🧪 Testing User Agent Rotation")
    print("="*80)
    print()
    
    # Test 5 different user agents
    for i in range(5):
        headers = get_reddit_headers()
        cookies = get_reddit_cookies()
        
        print(f"Test {i+1}/5")
        print("-"*80)
        print(f"User-Agent: {headers['User-Agent'][:60]}...")
        print(f"Cookies: {cookies}")
        print()
        
        try:
            async with httpx.AsyncClient(
                proxy=CRAWLER_PROXY,
                timeout=10.0,
                verify=False,
                follow_redirects=True,
                cookies=cookies
            ) as client:
                response = await client.get(
                    "https://www.reddit.com/r/python/about.json",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    subs = data.get("data", {}).get("subscribers", 0)
                    print(f"✅ SUCCESS! Status: {response.status_code}")
                    print(f"   r/python has {subs:,} subscribers")
                elif response.status_code == 404:
                    print(f"⚠️  404 - Reddit pretending sub doesn't exist (bot detection)")
                elif response.status_code == 403:
                    print(f"⚠️  403 - Forbidden (IP or headers blocked)")
                else:
                    print(f"⚠️  HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
        
        # Small delay between tests
        if i < 4:
            await asyncio.sleep(2)
    
    print("="*80)
    print("Test complete!")
    print()
    print("📊 Summary:")
    print("  - If all 5 tests show SUCCESS: ✅ User agents working!")
    print("  - If any show 404/403: ⚠️  Proxy IP might be burned")
    print("  - If errors: ❌ Check proxy credentials or network")
    print()

if __name__ == "__main__":
    asyncio.run(test_user_agents())



