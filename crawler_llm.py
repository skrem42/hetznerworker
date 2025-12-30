#!/usr/bin/env python3
"""
Crawler + LLM Worker
Script 2: Discovers new subreddits via JSON endpoints + enriches with LLM analysis.
Uses SOAX proxies with aggressive retry logic.
"""
import asyncio
import logging
import sys
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Set

from supabase_client import SupabaseClient
from llm_analyzer import SubredditLLMAnalyzer
from config import (
    CRAWLER_PROXY,
    CRAWLER_ROTATION_URL,
    CRAWLER_BATCH_SIZE,
    CRAWLER_TIMEOUT_SECONDS,
    CRAWLER_RETRY_MAX,
    CRAWLER_MIN_SUBSCRIBERS,
    CRAWLER_DELAY_BETWEEN_BATCHES,
    LLM_BATCH_SIZE,
    LLM_INTERVAL_SECONDS,
    LLM_MAX_CONCURRENT,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/crawler_llm.log")
    ]
)
logger = logging.getLogger(__name__)


class CrawlerLLM:
    """
    Combined crawler and LLM worker.
    
    Task 1: Discover new subreddits via JSON API (continuous)
    Task 2: Enrich subreddits with LLM analysis (periodic)
    """
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.llm_analyzer = SubredditLLMAnalyzer(reddit_proxy=CRAWLER_PROXY)
        
        # ProxyEmpire mobile proxy
        self.proxy = CRAWLER_PROXY
        self.rotation_url = CRAWLER_ROTATION_URL
        self.rotation_count = 0
        
        # Tracking (session-only - will reload existing from DB on first run)
        self.existing_subs: Set[str] = set()
        self.existing_subs_loaded = False
        
        # Stats
        self.crawler_stats = {
            "discovered": 0,
            "updated": 0,
            "failed": 0,
            "start_time": datetime.now(timezone.utc),
        }
        
        self.llm_stats = {
            "analyzed": 0,
            "failed": 0,
        }
    
    async def rotate_proxy(self):
        """Rotate ProxyEmpire IP."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.rotation_url)
                if response.status_code == 200:
                    self.rotation_count += 1
                    logger.info(f"🔄 ProxyEmpire IP rotated (rotation #{self.rotation_count})")
                else:
                    logger.warning(f"Failed to rotate IP: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"Error rotating IP: {e}")
    
    async def fetch_with_retry(self, url: str, max_retries: int = None) -> Optional[dict]:
        """
        Fetch URL with aggressive retry logic and proxy rotation.
        Non-blocking - returns None after max retries.
        """
        max_retries = max_retries or CRAWLER_RETRY_MAX
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    proxy=self.proxy,
                    timeout=CRAWLER_TIMEOUT_SECONDS,
                    verify=False,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        return response.json()
                    
                    elif response.status_code in [403, 429]:
                        logger.warning(f"HTTP {response.status_code} (attempt {attempt+1}/{max_retries}) - rotating IP")
                        await self.rotate_proxy()
                        await asyncio.sleep(5)  # Wait for IP to change
                    
                    else:
                        logger.warning(f"HTTP {response.status_code} for {url}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout (attempt {attempt+1}/{max_retries}) - rotating IP")
                await self.rotate_proxy()
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.warning(f"Error (attempt {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(2)
        
        # Give up after max retries
        logger.error(f"Failed after {max_retries} attempts: {url}")
        return None
    
    async def discover_subreddit_info(self, subreddit_name: str) -> Optional[dict]:
        """
        Fetch subreddit info from /about.json endpoint.
        Returns basic info to add to queue.
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        
        data = await self.fetch_with_retry(url)
        if not data:
            return None
        
        try:
            sub_data = data.get("data", {})
            
            # Skip if not NSFW
            if not sub_data.get("over18", False):
                return None
            
            # Skip if too small
            subscribers = sub_data.get("subscribers", 0)
            if subscribers < CRAWLER_MIN_SUBSCRIBERS:
                return None
            
            return {
                "subreddit_name": subreddit_name.lower(),
                "subscribers": subscribers,
                "description": sub_data.get("public_description", ""),
            }
            
        except Exception as e:
            logger.error(f"Error parsing data for r/{subreddit_name}: {e}")
            return None
    
    async def discover_from_user(self, username: str) -> List[str]:
        """
        Discover subreddits from a user's post history.
        Returns list of unique subreddit names.
        """
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit=100"
        
        data = await self.fetch_with_retry(url)
        if not data:
            return []
        
        try:
            posts = data.get("data", {}).get("children", [])
            subreddits = set()
            
            for post in posts:
                post_data = post.get("data", {})
                subreddit = post_data.get("subreddit")
                over_18 = post_data.get("over_18", False)
                
                if subreddit and over_18:
                    subreddits.add(subreddit.lower())
            
            return list(subreddits)
            
        except Exception as e:
            logger.error(f"Error parsing user data for u/{username}: {e}")
            return []
    
    async def load_existing_subs(self):
        """Load all existing subreddit names from DB into memory cache."""
        try:
            logger.info("Loading existing subreddits from database...")
            
            all_subs = []
            offset = 0
            page_size = 1000
            
            while True:
                result = self.supabase.client.table("subreddit_queue").select(
                    "subreddit_name"
                ).range(offset, offset + page_size - 1).execute()
                
                if not result.data or len(result.data) == 0:
                    break
                
                all_subs.extend([row["subreddit_name"].lower() for row in result.data])
                
                if len(result.data) < page_size:
                    break
                
                offset += page_size
            
            self.existing_subs = set(all_subs)
            self.existing_subs_loaded = True
            logger.info(f"Loaded {len(self.existing_subs):,} existing subreddits from database")
            
        except Exception as e:
            logger.error(f"Error loading existing subs: {e}")
            self.existing_subs = set()
    
    async def discover_subreddits(self):
        """
        Main discovery loop - continuously finds new subreddits.
        """
        logger.info("Starting subreddit discovery...")
        
        # Load existing subs on first run
        if not self.existing_subs_loaded:
            await self.load_existing_subs()
        
        while True:
            try:
                # Get some existing subreddits from queue to bootstrap discovery
                existing = await self.supabase.get_pending_intel_scrapes(limit=10)
                
                if not existing:
                    logger.info("No subreddits to bootstrap from. Waiting 60s...")
                    await asyncio.sleep(60)
                    continue
                
                for sub in existing:
                    subreddit_name = sub["subreddit_name"]
                    
                    # Get recent posts from this subreddit
                    posts_url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit=25"
                    posts_data = await self.fetch_with_retry(posts_url)
                    
                    if not posts_data:
                        continue
                    
                    # Extract unique authors
                    posts = posts_data.get("data", {}).get("children", [])
                    authors = set()
                    
                    for post in posts:
                        author = post.get("data", {}).get("author")
                        if author and author != "[deleted]":
                            authors.add(author)
                    
                    logger.info(f"Found {len(authors)} authors in r/{subreddit_name}")
                    
                    # Discover subreddits from each author
                    for author in list(authors)[:5]:  # Sample 5 authors
                        discovered_subs = await self.discover_from_user(author)
                        
                        for new_sub in discovered_subs:
                            # Skip if already in DB
                            if new_sub in self.existing_subs:
                                continue
                            
                            # Fetch subreddit info
                            sub_info = await self.discover_subreddit_info(new_sub)
                            
                            if sub_info:
                                # Check one more time in case it was just added
                                is_new = new_sub not in self.existing_subs
                                
                                # Add to queue (upsert)
                                success = await self.supabase.add_subreddit_to_queue(
                                    sub_info["subreddit_name"],
                                    sub_info["subscribers"]
                                )
                                
                                if success:
                                    self.existing_subs.add(new_sub)
                                    
                                    if is_new:
                                        self.crawler_stats["discovered"] += 1
                                        logger.info(
                                            f"✓ Discovered r/{new_sub} "
                                            f"({sub_info['subscribers']:,} subscribers)"
                                        )
                                    else:
                                        self.crawler_stats["updated"] += 1
                                        logger.debug(
                                            f"↻ Updated r/{new_sub} "
                                            f"({sub_info['subscribers']:,} subscribers)"
                                        )
                            
                            # Small delay to avoid rate limits
                            await asyncio.sleep(0.5)
                    
                    # Delay between subreddits
                    await asyncio.sleep(CRAWLER_DELAY_BETWEEN_BATCHES)
                
                # Log stats periodically
                if self.crawler_stats["discovered"] % 10 == 0:
                    self.log_crawler_stats()
                
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(60)
    
    async def run_llm_analysis(self):
        """
        Periodic LLM analysis loop.
        Runs every LLM_INTERVAL_SECONDS to enrich subreddits.
        """
        logger.info("Starting LLM analysis loop...")
        
        while True:
            try:
                await asyncio.sleep(LLM_INTERVAL_SECONDS)
                
                # Get subreddits missing LLM data
                missing_llm = await self.supabase.get_subs_missing_llm(limit=LLM_BATCH_SIZE)
                
                if not missing_llm:
                    logger.info("No subreddits need LLM analysis")
                    continue
                
                logger.info(f"\n{'='*80}")
                logger.info(f"Running LLM analysis on {len(missing_llm)} subreddits")
                logger.info(f"{'='*80}")
                
                # Process in smaller concurrent batches
                semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENT)
                
                async def analyze_one(sub_data):
                    async with semaphore:
                        await self.safe_llm_analyze(sub_data)
                
                tasks = [analyze_one(sub) for sub in missing_llm]
                await asyncio.gather(*tasks)
                
                self.log_llm_stats()
                
            except Exception as e:
                logger.error(f"Error in LLM analysis loop: {e}")
                await asyncio.sleep(60)
    
    async def safe_llm_analyze(self, sub_data: dict):
        """
        Analyze a subreddit with LLM with error handling.
        Non-blocking - always returns.
        """
        subreddit_name = sub_data["subreddit_name"]
        
        try:
            logger.info(f"Analyzing r/{subreddit_name}...")
            
            result = await self.llm_analyzer.analyze_subreddit(
                subreddit_name=subreddit_name,
                description=sub_data.get("description", ""),
                subscribers=sub_data.get("subscribers", 0),
            )
            
            if result:
                # Update database with LLM results
                update_data = {
                    "subreddit_name": subreddit_name,
                    "verification_required": result.get("verification_required"),
                    "sellers_allowed": result.get("sellers_allowed"),
                    "niche_categories": result.get("niche_categories"),
                    "llm_analysis_confidence": result.get("confidence"),
                    "llm_analysis_reasoning": result.get("reasoning"),
                }
                
                await self.supabase.upsert_subreddit_intel(update_data)
                self.llm_stats["analyzed"] += 1
                
                logger.info(
                    f"✓ r/{subreddit_name}: "
                    f"verification={result.get('verification_required')}, "
                    f"sellers={result.get('sellers_allowed')}"
                )
            else:
                logger.warning(f"LLM analysis returned no result for r/{subreddit_name}")
                self.llm_stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"Error analyzing r/{subreddit_name}: {e}")
            self.llm_stats["failed"] += 1
    
    def log_crawler_stats(self):
        """Log crawler statistics."""
        runtime = (datetime.now(timezone.utc) - self.crawler_stats["start_time"]).total_seconds()
        hours = runtime / 3600
        rate = self.crawler_stats["discovered"] / hours if hours > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info("CRAWLER STATS")
        logger.info(f"  New:        {self.crawler_stats['discovered']}")
        logger.info(f"  Updated:    {self.crawler_stats['updated']}")
        logger.info(f"  Failed:     {self.crawler_stats['failed']}")
        logger.info(f"  In DB:      {len(self.existing_subs):,}")
        logger.info(f"  Rate:       {rate:.1f} new/hour")
        logger.info(f"  Runtime:    {hours:.1f}h")
        logger.info(f"{'='*80}\n")
    
    def log_llm_stats(self):
        """Log LLM statistics."""
        logger.info(f"\n{'='*80}")
        logger.info("LLM STATS")
        logger.info(f"  Analyzed: {self.llm_stats['analyzed']}")
        logger.info(f"  Failed:   {self.llm_stats['failed']}")
        logger.info(f"{'='*80}\n")
    
    async def run(self):
        """Main entry point - runs both tasks in parallel."""
        logger.info("="*80)
        logger.info("CRAWLER + LLM WORKER STARTING")
        logger.info(f"  Crawler Batch: {CRAWLER_BATCH_SIZE}")
        logger.info(f"  LLM Batch: {LLM_BATCH_SIZE}")
        logger.info(f"  LLM Interval: {LLM_INTERVAL_SECONDS}s")
        logger.info(f"  Proxy: ProxyEmpire Mobile")
        logger.info("="*80)
        
        # Run both tasks in parallel
        discovery_task = asyncio.create_task(self.discover_subreddits())
        llm_task = asyncio.create_task(self.run_llm_analysis())
        
        try:
            await asyncio.gather(discovery_task, llm_task)
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
            discovery_task.cancel()
            llm_task.cancel()


async def main():
    """Entry point."""
    worker = CrawlerLLM()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

