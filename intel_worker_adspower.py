#!/usr/bin/env python3
"""
Intel Worker with AdsPower Integration
Script 1: Scrapes subreddit metrics using AdsPower managed browsers with ProxyEmpire.
"""
import asyncio
import logging
import sys
import re
from datetime import datetime, timezone
from typing import Optional, Dict
from playwright.async_api import async_playwright, Page

from adspower_client import AdsPowerClient
from supabase_client import SupabaseClient
from config import (
    ADSPOWER_PROFILE_IDS,
    INTEL_BATCH_SIZE,
    INTEL_TIMEOUT_SECONDS,
    INTEL_CONCURRENT,
    INTEL_DELAY_BETWEEN_BATCHES,
    PROXYEMPIRE_ROTATION_URL,
    LOG_LEVEL,
    LOG_FORMAT,
    HEALTH_CHECK_INTERVAL,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/intel_worker.log")
    ]
)
logger = logging.getLogger(__name__)


class IntelWorkerAdsPower:
    """
    Intel worker that uses AdsPower browsers for scraping.
    Keeps 10 browsers open and cycles through them.
    """
    
    def __init__(self):
        self.adspower = AdsPowerClient()
        self.supabase = SupabaseClient()
        
        # Browser management
        self.active_browsers: Dict[str, Dict] = {}  # profile_id -> {page, playwright_browser}
        self.browser_queue = asyncio.Queue()  # Available browsers
        
        # Stats
        self.stats = {
            "scraped": 0,
            "failed": 0,
            "retries": 0,
            "start_time": datetime.now(timezone.utc),
        }
    
    async def initialize_browsers(self):
        """
        Launch all AdsPower browser profiles and connect via CDP.
        Keeps browsers open for the entire session.
        """
        logger.info("="*80)
        logger.info("Initializing AdsPower Browsers")
        logger.info("="*80)
        
        playwright = await async_playwright().start()
        
        for profile_id in ADSPOWER_PROFILE_IDS:
            try:
                # Check if placeholder
                if profile_id.startswith("PROFILE_"):
                    logger.warning(f"Skipping placeholder profile: {profile_id}")
                    continue
                
                logger.info(f"Starting browser for profile {profile_id}...")
                
                # Start browser via AdsPower API
                browser_data = await self.adspower.start_profile(profile_id)
                if not browser_data:
                    logger.error(f"Failed to start profile {profile_id}")
                    continue
                
                # Get WebSocket endpoint
                ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
                debug_port = browser_data.get("debug_port")
                
                if not ws_endpoint:
                    logger.error(f"No WebSocket endpoint for profile {profile_id}")
                    continue
                
                # Connect Playwright to the browser
                browser = await playwright.chromium.connect_over_cdp(ws_endpoint)
                
                # Get the default context and first page
                contexts = browser.contexts
                if not contexts:
                    logger.error(f"No contexts available for profile {profile_id}")
                    await browser.close()
                    continue
                
                context = contexts[0]
                pages = context.pages
                
                if not pages:
                    # Create a new page if none exist
                    page = await context.new_page()
                else:
                    page = pages[0]
                
                # Store browser and page
                self.active_browsers[profile_id] = {
                    "page": page,
                    "browser": browser,
                    "context": context,
                    "profile_id": profile_id,
                }
                
                # Add to queue
                await self.browser_queue.put(profile_id)
                
                logger.info(f"[OK] Browser {profile_id} ready (port {debug_port})")
                
            except Exception as e:
                logger.error(f"Error initializing browser {profile_id}: {e}")
                continue
        
        active_count = len(self.active_browsers)
        logger.info("="*80)
        logger.info(f"Initialized {active_count}/{len(ADSPOWER_PROFILE_IDS)} browsers")
        logger.info("="*80)
        
        if active_count == 0:
            raise RuntimeError("No browsers initialized! Check AdsPower setup.")
    
    async def scrape_subreddit(self, subreddit_name: str, page: Page) -> Optional[Dict]:
        """
        Scrape metrics for a single subreddit.
        
        Args:
            subreddit_name: Name of subreddit
            page: Playwright page to use
            
        Returns:
            Dict with scraped data or None on failure
        """
        url = f"https://www.reddit.com/r/{subreddit_name}"
        
        try:
            # Navigate to subreddit - use domcontentloaded (faster, don't wait for everything)
            response = await page.goto(url, wait_until="domcontentloaded", timeout=INTEL_TIMEOUT_SECONDS * 1000)
            
            if not response or response.status != 200:
                logger.warning(f"Failed to load r/{subreddit_name}: {response.status if response else 'No response'}")
                return None
            
            # Handle NSFW consent dialogs immediately
            await self._handle_nsfw_consent(page)
            
            # Scroll to trigger lazy loading of stats (do this early)
            await page.evaluate('window.scrollTo(0, 500)')
            await asyncio.sleep(0.5)
            await page.evaluate('window.scrollTo(0, 0)')
            
            # Wait for stats elements to appear - THIS IS WHAT WE CARE ABOUT
            # As soon as they're there, we proceed!
            try:
                await page.wait_for_selector(
                    '[slot="weekly-active-users-count"], [slot="weekly-posts-count"], [slot="weekly-contributions-count"]',
                    timeout=45000,  # Give it up to 45s to find stats
                    state="attached"
                )
                logger.debug(f"[OK] Stats elements found for r/{subreddit_name}")
            except:
                # Stats might not be available, but continue anyway
                logger.debug(f"Stats not found for r/{subreddit_name}, continuing...")
                # Give it a couple more seconds in case they're still loading
                await asyncio.sleep(2)
            
            # Extract data immediately (don't wait for anything else)
            content = await page.content()
            page_title = await page.title()
            
            # Check if subreddit is banned/private/deleted/quarantined
            page_title_lower = page_title.lower()
            content_lower = content.lower()
            
            # Check for explicit ban/private messages
            ban_messages = [
                "this community has been banned",
                "this community is private",
                "this subreddit has been banned",
                "you must be invited",
                "this community has been set to private",
                "r/all - reddit",  # Redirected to r/all means doesn't exist
                "page not found",
                "sorry, this community is private",
            ]
            
            is_unavailable = any(msg in content_lower for msg in ban_messages)
            
            # Also check page title
            if not is_unavailable:
                title_indicators = ["banned", "private", "not found", "reddit - dive into anything"]
                # If title is generic Reddit title (not subreddit name), something's wrong
                is_unavailable = any(indicator in page_title_lower for indicator in title_indicators) and subreddit_name.lower() not in page_title_lower
            
            # If page loaded but has absolutely no subreddit-specific content, it's likely banned/private
            if not is_unavailable:
                # Check if page has basic subreddit elements
                has_sub_header = "shreddit-subreddit-header" in content or f"r/{subreddit_name}" in content_lower
                has_any_posts = "shreddit-post" in content or "slot=" in content
                
                # If no subreddit content at all, it's unavailable
                if not has_sub_header and not has_any_posts:
                    is_unavailable = True
                    logger.debug(f"r/{subreddit_name}: No subreddit content found on page")
            
            if is_unavailable:
                logger.warning(f"[X] r/{subreddit_name}: Subreddit is unavailable (banned/private/deleted) - page title: '{page_title[:60]}'")
                return {"permanently_failed": True, "error": "Subreddit banned/private/deleted"}
            
            data = {
                "subreddit_name": subreddit_name.lower(),
                "display_name": f"r/{subreddit_name}",
                "last_scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Extract weekly visitors
            visitors_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
            if visitors_match:
                data["weekly_visitors"] = self._parse_metric(visitors_match.group(1))
            
            # Extract weekly contributions
            for pattern in [
                r'slot="weekly-posts-count"[^>]*>([^<]+)<',
                r'slot="weekly-contributions-count"[^>]*>([^<]+)<',
            ]:
                contrib_match = re.search(pattern, content)
                if contrib_match:
                    data["weekly_contributions"] = self._parse_metric(contrib_match.group(1))
                    break
            
            # Only mark as completed if we got at least some data
            if not data.get("weekly_visitors") and not data.get("weekly_contributions"):
                logger.warning(f"X r/{subreddit_name}: No metrics found, will retry")
                return None
            
            # Mark as completed
            data["scrape_status"] = "completed"
            
            # Calculate competition score
            if data.get("weekly_visitors") and data.get("weekly_contributions"):
                data["competition_score"] = round(
                    data["weekly_contributions"] / data["weekly_visitors"], 6
                )
            
            logger.info(
                f"[OK] r/{subreddit_name}: "
                f"{data.get('weekly_visitors', 'N/A')} visitors, "
                f"{data.get('weekly_contributions', 'N/A')} contributions"
            )
            
            return data
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout scraping r/{subreddit_name}")
            return None
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")
            return None
    
    async def _handle_nsfw_consent(self, page: Page):
        """Handle NSFW consent dialogs."""
        consent_selectors = [
            'button:has-text("Yes, I\'m over 18")',
            'button:has-text("I am 18 or older")',
            '[data-testid="over-18-button"]',
        ]
        for selector in consent_selectors:
            try:
                await page.click(selector, timeout=3000)
                # Wait for page to reload after consent
                await asyncio.sleep(2)
                return  # Exit after first successful click
            except:
                pass
    
    def _parse_metric(self, text: str) -> Optional[int]:
        """Parse metrics like '1.2K' to integer."""
        if not text:
            return None
        
        text = text.strip().replace(',', '')
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, mult in multipliers.items():
            if suffix in text.upper():
                try:
                    num = float(text.upper().replace(suffix, ''))
                    return int(num * mult)
                except:
                    pass
        
        try:
            return int(text)
        except:
            return None
    
    async def process_batch(self, subreddits: list):
        """Process a batch of subreddits in parallel using available browsers."""
        tasks = []
        
        for sub in subreddits:
            task = self.safe_scrape_subreddit(sub["subreddit_name"])
            tasks.append(task)
        
        # Process all in parallel
        await asyncio.gather(*tasks)
    
    async def safe_scrape_subreddit(self, subreddit_name: str):
        """
        Scrape a subreddit with timeout and error handling.
        Non-blocking - always returns, never crashes.
        If scraping fails, marks for retry and moves on.
        After 3 failed attempts with same error, marks as permanently failed.
        """
        profile_id = None
        
        try:
            # Check how many times this sub has failed before
            failure_count = 0
            try:
                retry_check = self.supabase.client.table("nsfw_subreddit_intel").select(
                    "error_message"
                ).eq("subreddit_name", subreddit_name.lower()).execute()
                
                if retry_check.data and len(retry_check.data) > 0:
                    error_msg = retry_check.data[0].get("error_message", "")
                    # Count how many times "No metrics" appears (each retry adds it)
                    if "Scrape returned no data" in error_msg or "No metrics" in error_msg:
                        failure_count = error_msg.count("No metrics") + error_msg.count("Scrape returned no data")
            except:
                pass
            
            # Acquire browser from queue (with timeout)
            async with asyncio.timeout(60):
                profile_id = await self.browser_queue.get()
            
            browser_ctx = self.active_browsers.get(profile_id)
            if not browser_ctx:
                logger.error(f"Browser {profile_id} not found!")
                return
            
            page = browser_ctx["page"]
            
            # Scrape with timeout
            async with asyncio.timeout(INTEL_TIMEOUT_SECONDS):
                result = await self.scrape_subreddit(subreddit_name, page)
            
            if result:
                # Check if this is a permanently failed sub (banned/private/deleted)
                if result.get("permanently_failed"):
                    await self.supabase.mark_intel_failed(
                        subreddit_name, 
                        result.get("error", "Subreddit unavailable")
                    )
                    self.stats["failed"] += 1
                    logger.info(f"Permanently failed r/{subreddit_name}")
                else:
                    # Save to database
                    await self.supabase.upsert_subreddit_intel(result)
                    self.stats["scraped"] += 1
            else:
                # If this sub has failed 3+ times, mark as permanently failed
                if failure_count >= 3:
                    logger.warning(f"[X] r/{subreddit_name}: Failed {failure_count} times - marking as permanently failed")
                    await self.supabase.mark_intel_failed(subreddit_name, f"No metrics after {failure_count} attempts")
                    self.stats["failed"] += 1
                else:
                    # Mark for retry
                    await self.supabase.mark_for_retry(subreddit_name, "Scrape returned no data")
                    self.stats["retries"] += 1
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout on r/{subreddit_name}, moving on")
            await self.supabase.mark_for_retry(subreddit_name, "Timeout")
            self.stats["retries"] += 1
            
        except Exception as e:
            logger.error(f"Error on r/{subreddit_name}: {e}")
            await self.supabase.mark_for_retry(subreddit_name, str(e))
            self.stats["failed"] += 1
            
        finally:
            # Always return browser to queue
            if profile_id:
                await self.browser_queue.put(profile_id)
    
    async def health_check_loop(self):
        """Periodically check browser health."""
        while True:
            try:
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
                logger.debug("Running browser health checks...")
                healthy_count = 0
                busy_count = 0
                failed_count = 0
                
                for profile_id, browser_ctx in list(self.active_browsers.items()):
                    try:
                        page = browser_ctx["page"]
                        browser = browser_ctx["browser"]
                        
                        # Check if browser is still connected
                        if not browser.is_connected():
                            logger.error(f"Browser {profile_id} disconnected!")
                            failed_count += 1
                            continue
                        
                        # Try to evaluate - if page is navigating, this will fail gracefully
                        async with asyncio.timeout(3):
                            result = await page.evaluate("1+1")
                            if result == 2:
                                healthy_count += 1
                    except asyncio.TimeoutError:
                        # Page might be navigating or slow
                        busy_count += 1
                        logger.debug(f"Browser {profile_id} timeout (likely busy scraping)")
                    except Exception as e:
                        error_msg = str(e)
                        # "Execution context was destroyed" means page is navigating - this is OK
                        if "Execution context was destroyed" in error_msg or "navigation" in error_msg.lower():
                            busy_count += 1
                            logger.debug(f"Browser {profile_id} busy (navigating)")
                        else:
                            # Actually unhealthy
                            failed_count += 1
                            logger.warning(f"Browser {profile_id} unhealthy: {error_msg[:100]}")
                
                logger.info(f"Health check: {healthy_count} idle/healthy, {busy_count} busy, {failed_count} failed (total: {len(self.active_browsers)})")
                        
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def run(self):
        """Main worker loop."""
        logger.info("="*80)
        logger.info("INTEL WORKER STARTING (AdsPower Mode)")
        logger.info(f"  Batch Size: {INTEL_BATCH_SIZE}")
        logger.info(f"  Concurrent: {INTEL_CONCURRENT}")
        logger.info(f"  Timeout: {INTEL_TIMEOUT_SECONDS}s")
        logger.info("="*80)
        
        # Initialize browsers
        await self.initialize_browsers()
        
        # Start health check loop
        health_task = asyncio.create_task(self.health_check_loop())
        
        try:
            while True:
                # Get pending subreddits
                pending = await self.supabase.get_pending_intel_scrapes(limit=INTEL_BATCH_SIZE)
                
                if not pending:
                    logger.info("No pending subreddits. Waiting 60s...")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"\n{'='*80}")
                logger.info(f"Processing batch of {len(pending)} subreddits")
                logger.info(f"{'='*80}")
                
                # Process batch
                await self.process_batch(pending)
                
                # Log stats
                self.log_stats()
                
                # Brief delay between batches
                await asyncio.sleep(INTEL_DELAY_BETWEEN_BATCHES)
                
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
        finally:
            # Cleanup
            health_task.cancel()
            await self.cleanup()
    
    def log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
        hours = runtime / 3600
        rate = self.stats["scraped"] / hours if hours > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info("STATS")
        logger.info(f"  Scraped:  {self.stats['scraped']}")
        logger.info(f"  Retries:  {self.stats['retries']}")
        logger.info(f"  Failed:   {self.stats['failed']}")
        logger.info(f"  Rate:     {rate:.1f} subs/hour")
        logger.info(f"  Runtime:  {hours:.1f}h")
        logger.info(f"  Browsers: {len(self.active_browsers)}/{len(ADSPOWER_PROFILE_IDS)}")
        logger.info(f"{'='*80}\n")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up...")
        
        # Close all browsers
        for profile_id, browser_ctx in self.active_browsers.items():
            try:
                await browser_ctx["browser"].close()
                await self.adspower.stop_profile(profile_id)
                logger.info(f"Closed browser {profile_id}")
            except Exception as e:
                logger.error(f"Error closing browser {profile_id}: {e}")
        
        await self.adspower.close()
        logger.info("Cleanup complete")


async def main():
    """Entry point."""
    worker = IntelWorkerAdsPower()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

