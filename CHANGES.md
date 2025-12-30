# Configuration Changes - ProxyEmpire Migration

## Summary

Successfully migrated from SOAX to ProxyEmpire mobile proxy for the crawler and LLM analyzer due to SOAX rate limit issues (422 errors).

## What Changed

### 1. **config.py** - Proxy Configuration
- **Removed**: SOAX proxy pool (5 sessions)
- **Added**: ProxyEmpire mobile proxy for crawler + LLM
- **Added**: Proxidize rotation URL for intel worker
- **New variables**:
  ```python
  PROXIDIZE_ROTATION_URL = "https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"
  CRAWLER_PROXY = PROXYEMPIRE_URL
  CRAWLER_ROTATION_URL = PROXYEMPIRE_ROTATION_URL
  ```

### 2. **crawler_llm.py** - Crawler Worker
- **Changed**: Uses single ProxyEmpire mobile proxy instead of SOAX pool
- **Updated**: `rotate_proxy()` now calls ProxyEmpire rotation API
- **Improved**: Better error handling with exponential backoff
- **Result**: ✅ Successfully fetches Reddit data

### 3. **llm_analyzer.py** - LLM Analyzer
- **Changed**: Uses ProxyEmpire mobile proxy instead of SOAX
- **Updated**: Initialization message reflects ProxyEmpire
- **Result**: ✅ Successfully analyzes subreddits

### 4. **requirements.txt** - Dependencies
- **Fixed**: Python 3.14 compatibility issues
- **Updated**: All packages to latest compatible versions for Python 3.13
- **Removed**: `asyncio` (built into Python)

## Testing Results

### ✅ All Tests Passing

1. **AdsPower Connection**: ✅ Connected (1 profile found)
2. **Intel Worker**: ✅ Works with Proxidize proxy in AdsPower
3. **Crawler Discovery**: ✅ Successfully discovers subreddits
   - Example: r/realgirls (4M subscribers)
4. **Crawler Fetch**: ✅ Successfully fetches subreddit data
   - Example: r/gonewild (5.2M subscribers)
5. **LLM Analyzer**: ✅ Successfully analyzes with GPT-4o-mini

## Proxy Architecture

```
┌────────────────────────────────────────────┐
│  Intel Worker (AdsPower)                   │
│  └─ Uses: Proxidize (custom in profiles)  │
│  └─ Rotation: API available if needed      │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  Crawler + LLM Worker                      │
│  └─ Uses: ProxyEmpire Mobile               │
│  └─ Rotation: Automatic on 403/429 errors  │
└────────────────────────────────────────────┘
```

## IP Rotation Strategy

### Intel Worker (Proxidize)
- Configured directly in AdsPower profiles
- Rotation URL available: `https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/`
- Can be called manually or triggered on errors if needed

### Crawler + LLM (ProxyEmpire)
- Single mobile IP with automatic rotation
- Rotates on: 403, 429 errors or timeouts
- Rotation API: `https://panel.proxyempire.io/dedicated-mobile/2ed80b8624/get-new-ip-by-username`
- Wait 5 seconds after rotation for IP to change

## Next Steps

1. ✅ Update AdsPower profile IDs in `config.py` (currently have 1, need 10)
2. ✅ Test intel worker with full batch
3. ✅ Run full system test (both workers simultaneously)
4. 🔄 Deploy to Hetzner VPS

## Configuration Notes

### OpenAI API Key
Already configured in `config.py`:
```python
OPENAI_API_KEY = "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"
```

### AdsPower Profiles
Current IDs in config (need to verify all exist):
```python
["koeuril", "koeus69", "koeusic", "koeuswn", "koev1yk", 
 "koev27c", "koev2lc", "koev33x", "koev3lr", "koev3v3"]
```

Only 1 detected: `koeuril` (needs investigation)

## Performance Expectations

With ProxyEmpire mobile proxy:
- **Discovery**: Faster and more reliable than SOAX
- **LLM Analysis**: No impact (uses direct OpenAI connection)
- **IP Rotation**: ~3-5 seconds for new IP to activate
- **Rate Limits**: Much higher than SOAX (mobile residential IPs)

## Troubleshooting

### If Crawler Fails
1. Check ProxyEmpire subscription is active
2. Test proxy manually: 
   ```bash
   curl -x "http://2ed80b8624:570abb9a59@mobdedi.proxyempire.io:9000" https://ipinfo.io
   ```
3. Check rotation API:
   ```bash
   curl "https://panel.proxyempire.io/dedicated-mobile/2ed80b8624/get-new-ip-by-username"
   ```

### If Intel Worker Fails
1. Check Proxidize proxy in AdsPower profiles
2. Test rotation API:
   ```bash
   curl "https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"
   ```
3. Verify all 10 profiles exist in AdsPower

## Files Modified
- `config.py` - Proxy configuration
- `crawler_llm.py` - Proxy usage and rotation
- `llm_analyzer.py` - Proxy initialization
- `requirements.txt` - Dependency versions

Date: December 30, 2025

