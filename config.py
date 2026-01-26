"""
Configuration for Hetzner Worker Setup
Centralized configuration for both intel worker and crawler.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")

# =============================================================================
# ADSPOWER API CONFIGURATION
# =============================================================================
ADSPOWER_API_URL = os.getenv("ADSPOWER_API_URL", "http://local.adspower.net:50325")

# AdsPower Profile IDs - Get these from AdsPower UI after creating profiles
# To get profile IDs: Open AdsPower → Right click profile → Copy User ID
# Set in .env as: ADSPOWER_PROFILE_IDS=id1,id2,id3
_profile_ids_str = os.getenv("ADSPOWER_PROFILE_IDS", "")
if not _profile_ids_str:
    raise ValueError("ADSPOWER_PROFILE_IDS must be set in .env file (comma-separated)")
ADSPOWER_PROFILE_IDS = [pid.strip() for pid in _profile_ids_str.split(",") if pid.strip()]

# =============================================================================
# PROXY CONFIGURATION
# =============================================================================

# Proxidize (for Intel Worker - configured in AdsPower profiles)
# IP rotation URL for when needed
PROXIDIZE_ROTATION_URL = os.getenv("PROXIDIZE_ROTATION_URL")
if not PROXIDIZE_ROTATION_URL:
    raise ValueError("PROXIDIZE_ROTATION_URL must be set in .env file")

# ProxyEmpire Mobile Proxy (for Crawler + LLM)
# Using mobile proxy for better reliability with Reddit
PROXYEMPIRE_HOST = os.getenv("PROXYEMPIRE_HOST")
PROXYEMPIRE_PORT = int(os.getenv("PROXYEMPIRE_PORT", "9000"))
PROXYEMPIRE_USERNAME = os.getenv("PROXYEMPIRE_USERNAME")
PROXYEMPIRE_PASSWORD = os.getenv("PROXYEMPIRE_PASSWORD")

if not all([PROXYEMPIRE_HOST, PROXYEMPIRE_USERNAME, PROXYEMPIRE_PASSWORD]):
    raise ValueError("ProxyEmpire credentials must be set in .env file")

PROXYEMPIRE_URL = f"http://{PROXYEMPIRE_USERNAME}:{PROXYEMPIRE_PASSWORD}@{PROXYEMPIRE_HOST}:{PROXYEMPIRE_PORT}"
PROXYEMPIRE_ROTATION_URL = f"https://panel.proxyempire.io/dedicated-mobile/{PROXYEMPIRE_USERNAME}/get-new-ip-by-username"

# Crawler will use ProxyEmpire (single mobile IP with rotation)
CRAWLER_PROXY = PROXYEMPIRE_URL
CRAWLER_ROTATION_URL = PROXYEMPIRE_ROTATION_URL

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env file")

# =============================================================================
# WORKER SETTINGS
# =============================================================================

# Intel Worker (AdsPower)
INTEL_BATCH_SIZE = 4  # Number of subreddits to fetch per batch (2x browsers for buffer)
INTEL_TIMEOUT_SECONDS = 180  # Timeout per subreddit scrape (3 minutes max)
INTEL_CONCURRENT = 2  # Match number of active browsers
INTEL_DELAY_BETWEEN_BATCHES = 2  # Seconds between batches
INTEL_RETRY_MAX = 5  # Max retries before marking as failed

# Crawler (JSON endpoints)
CRAWLER_BATCH_SIZE = 50  # Subreddits to process per batch
CRAWLER_TIMEOUT_SECONDS = 15  # Timeout per request
CRAWLER_RETRY_MAX = 5  # Max retries per endpoint
CRAWLER_MIN_SUBSCRIBERS = 5000  # Minimum subscribers to crawl
CRAWLER_DELAY_BETWEEN_BATCHES = 1  # Seconds between batches

# LLM Analyzer
LLM_BATCH_SIZE = 10  # Subreddits to analyze per batch
LLM_INTERVAL_SECONDS = 600  # Run every 10 minutes
LLM_MAX_CONCURRENT = 5  # Concurrent LLM requests
LLM_RETRY_MAX = 3  # Max retries for LLM calls

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"

# =============================================================================
# MONITORING SETTINGS
# =============================================================================
MONITOR_REFRESH_SECONDS = 30  # Dashboard refresh interval
HEALTH_CHECK_INTERVAL = 60  # Browser health check interval

