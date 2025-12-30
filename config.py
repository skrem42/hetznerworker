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
SUPABASE_URL = "https://jmchmbwhnmlednaycxqh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU"

# =============================================================================
# ADSPOWER API CONFIGURATION
# =============================================================================
ADSPOWER_API_URL = "http://local.adspower.net:50325"

# AdsPower Profile IDs - Get these from AdsPower UI after creating profiles
# To get profile IDs: Open AdsPower → Right click profile → Copy User ID
ADSPOWER_PROFILE_IDS = [
    # Currently active browsers
    "koeuril",
    "koeus69",
    # Commented out - add more as needed
    # "koeusic",
    # "koeuswn",
    # "koev1yk",
    # "koev27c",
    # "koev2lc",
    # "koev33x",
    # "koev3lr",
    # "koev3v3",
]

# =============================================================================
# PROXY CONFIGURATION
# =============================================================================

# Proxidize (for Intel Worker - configured in AdsPower profiles)
# IP rotation URL for when needed
PROXIDIZE_ROTATION_URL = "https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/bea349dca02dadc7784c7e91d4f6b005/"

# ProxyEmpire Mobile Proxy (for Crawler + LLM)
# Using mobile proxy for better reliability with Reddit
PROXYEMPIRE_HOST = "mobdedi.proxyempire.io"
PROXYEMPIRE_PORT = 9000
PROXYEMPIRE_USERNAME = "2ed80b8624"
PROXYEMPIRE_PASSWORD = "570abb9a59"
PROXYEMPIRE_URL = f"http://{PROXYEMPIRE_USERNAME}:{PROXYEMPIRE_PASSWORD}@{PROXYEMPIRE_HOST}:{PROXYEMPIRE_PORT}"
PROXYEMPIRE_ROTATION_URL = f"https://panel.proxyempire.io/dedicated-mobile/{PROXYEMPIRE_USERNAME}/get-new-ip-by-username"

# Crawler will use ProxyEmpire (single mobile IP with rotation)
CRAWLER_PROXY = PROXYEMPIRE_URL
CRAWLER_ROTATION_URL = PROXYEMPIRE_ROTATION_URL

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = "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"

# =============================================================================
# WORKER SETTINGS
# =============================================================================

# Intel Worker (AdsPower)
INTEL_BATCH_SIZE = 6  # Number of subreddits to fetch per batch (3x browsers)
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

