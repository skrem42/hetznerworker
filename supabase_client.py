"""
Supabase client for Hetzner Worker.
Handles reading from subreddit_queue and writing to nsfw_subreddit_intel.
Includes retry logic and non-blocking error handling.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client with robust retry logic."""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # ==================== Subreddit Intel ====================

    async def upsert_subreddit_intel(self, data: dict) -> Optional[dict]:
        """Insert or update subreddit intelligence data."""
        try:
            intel_data = {
                "subreddit_name": data["subreddit_name"].lower(),
                "display_name": data.get("display_name"),
                "subscribers": data.get("subscribers"),
                "weekly_visitors": data.get("weekly_visitors"),
                "weekly_contributions": data.get("weekly_contributions"),
                "competition_score": data.get("competition_score"),
                "description": data.get("description"),
                "rules_count": data.get("rules_count", 0),
                "created_utc": data.get("created_utc"),
                "is_verified": data.get("is_verified", False),
                "allows_images": data.get("allows_images", True),
                "allows_videos": data.get("allows_videos", True),
                "allows_polls": data.get("allows_polls", True),
                "post_requirements": data.get("post_requirements", {}),
                "moderator_count": data.get("moderator_count", 0),
                "community_icon_url": data.get("community_icon_url"),
                "banner_url": data.get("banner_url"),
                "last_scraped_at": data.get("last_scraped_at", datetime.now(timezone.utc).isoformat()),
                "scrape_status": data.get("scrape_status", "completed"),
                "error_message": data.get("error_message"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                
                # LLM fields
                "verification_required": data.get("verification_required"),
                "sellers_allowed": data.get("sellers_allowed"),
                "niche_categories": data.get("niche_categories"),
                "llm_analysis_confidence": data.get("llm_analysis_confidence"),
                "llm_analysis_reasoning": data.get("llm_analysis_reasoning"),
            }
            
            result = self.client.table("nsfw_subreddit_intel").upsert(
                intel_data,
                on_conflict="subreddit_name"
            ).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error upserting subreddit intel {data.get('subreddit_name')}: {e}")
            return None

    async def mark_for_retry(self, subreddit_name: str, error_message: str) -> bool:
        """
        Mark a subreddit for retry.
        Sets scrape_status to 'pending' so it will be picked up again.
        """
        try:
            self.client.table("nsfw_subreddit_intel").upsert({
                "subreddit_name": subreddit_name.lower(),
                "scrape_status": "pending",
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="subreddit_name").execute()
            
            logger.debug(f"Marked {subreddit_name} for retry: {error_message}")
            return True
        except Exception as e:
            logger.error(f"Error marking for retry {subreddit_name}: {e}")
            return False

    async def mark_intel_failed(self, subreddit_name: str, error_message: str) -> bool:
        """Mark a subreddit intel scrape as failed permanently."""
        try:
            self.client.table("nsfw_subreddit_intel").upsert({
                "subreddit_name": subreddit_name.lower(),
                "scrape_status": "failed",
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="subreddit_name").execute()
            return True
        except Exception as e:
            logger.error(f"Error marking intel failed {subreddit_name}: {e}")
            return False

    async def get_pending_intel_scrapes(self, limit: int = 50, min_subscribers: int = 5000) -> list[dict]:
        """
        Get subreddits for intel scraping.
        Returns subreddits from queue that are NOT yet in intel table OR marked for retry.
        """
        try:
            # First try RPC function (faster but may have type issues in some DB versions)
            # If RPC fails, fallback method below will handle it
            result = self.client.rpc(
                "get_subreddits_not_in_intel",
                {
                    "p_limit": limit,
                    "p_min_subscribers": min_subscribers
                }
            ).execute()
            
            pending = result.data or []
            
            # If we have fewer than limit, also get pending/failed ones (retries)
            # BUT exclude permanently banned/private subs
            if len(pending) < limit:
                retry_result = self.client.table("nsfw_subreddit_intel").select(
                    "subreddit_name, subscribers, error_message"
                ).in_(
                    "scrape_status", ["pending", "failed"]
                ).order(
                    "subscribers", desc=True
                ).limit(limit - len(pending)).execute()
                
                if retry_result.data:
                    # Filter out permanently banned/private subs
                    for sub in retry_result.data:
                        error_msg = sub.get("error_message", "").lower()
                        # Skip if error indicates permanent failure
                        if any(term in error_msg for term in ["banned", "private", "deleted", "unavailable"]):
                            continue
                        pending.append(sub)
            
            return pending[:limit]
            
        except Exception as e:
            logger.debug(f"RPC unavailable, using fallback query")
            # Fallback to client-side filtering
            try:
                all_queue_subs = []
                page_size = 1000
                offset = 0
                
                while True:
                    queue_result = self.client.table("subreddit_queue").select(
                        "subreddit_name, subscribers"
                    ).gte(
                        "subscribers", min_subscribers
                    ).order(
                        "subscribers", desc=True
                    ).range(offset, offset + page_size - 1).execute()
                    
                    if not queue_result.data or len(queue_result.data) == 0:
                        break
                    
                    all_queue_subs.extend(queue_result.data)
                    
                    if len(queue_result.data) < page_size:
                        break
                    
                    offset += page_size
                
                logger.debug(f"Fetched {len(all_queue_subs)} subreddits from queue")
                
                # Get already scraped names
                all_intel_names = []
                intel_offset = 0
                
                while True:
                    intel_result = self.client.table("nsfw_subreddit_intel").select(
                        "subreddit_name, scrape_status, error_message"
                    ).range(intel_offset, intel_offset + page_size - 1).execute()
                    
                    if not intel_result.data or len(intel_result.data) == 0:
                        break
                    
                    all_intel_names.extend(intel_result.data)
                    
                    if len(intel_result.data) < page_size:
                        break
                    
                    intel_offset += page_size
                
                # Filter: not scraped OR pending/failed (for retry)
                # BUT exclude permanently banned/private subs
                scraped_names = set()
                for row in all_intel_names:
                    status = row.get("scrape_status")
                    error_msg = (row.get("error_message") or "").lower()
                    
                    # Exclude if completed
                    if status == "completed":
                        scraped_names.add(row["subreddit_name"].lower())
                    # Exclude if permanently failed (banned/private/deleted)
                    elif status == "failed" and any(term in error_msg for term in ["banned", "private", "deleted", "unavailable"]):
                        scraped_names.add(row["subreddit_name"].lower())
                
                pending = []
                for row in all_queue_subs:
                    if row["subreddit_name"].lower() not in scraped_names:
                        pending.append(row)
                        if len(pending) >= limit:
                            break
                
                return pending
            except Exception as e2:
                logger.error(f"Error getting pending intel scrapes: {e2}")
                return []

    async def get_subs_missing_llm(self, limit: int = 50) -> list[dict]:
        """Get subreddits missing LLM analysis."""
        try:
            result = self.client.table("nsfw_subreddit_intel").select(
                "subreddit_name, description, subscribers"
            ).is_(
                "verification_required", "null"
            ).not_.is_(
                "description", "null"
            ).order(
                "subscribers", desc=True
            ).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting subs missing LLM: {e}")
            return []

    async def add_subreddit_to_queue(self, subreddit_name: str, subscribers: int = 0) -> bool:
        """Add a new subreddit to the queue."""
        try:
            self.client.table("subreddit_queue").upsert({
                "subreddit_name": subreddit_name.lower(),
                "subscribers": subscribers,
                "status": "pending",
            }, on_conflict="subreddit_name").execute()
            
            return True
        except Exception as e:
            logger.error(f"Error adding {subreddit_name} to queue: {e}")
            return False

    async def get_intel_stats(self) -> dict:
        """Get statistics about the intel table."""
        try:
            total_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).execute()
            
            completed_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "completed").execute()
            
            pending_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "pending").execute()
            
            failed_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "failed").execute()
            
            return {
                "total": total_result.count or 0,
                "completed": completed_result.count or 0,
                "pending": pending_result.count or 0,
                "failed": failed_result.count or 0,
            }
        except Exception as e:
            logger.error(f"Error getting intel stats: {e}")
            return {"total": 0, "completed": 0, "pending": 0, "failed": 0}

    async def get_queue_stats(self) -> dict:
        """Get statistics about the queue."""
        try:
            total_result = self.client.table("subreddit_queue").select(
                "*", count="exact", head=True
            ).execute()
            
            pending_result = self.client.table("subreddit_queue").select(
                "*", count="exact", head=True
            ).eq("status", "pending").execute()
            
            completed_result = self.client.table("subreddit_queue").select(
                "*", count="exact", head=True
            ).eq("status", "completed").execute()
            
            return {
                "total": total_result.count or 0,
                "pending": pending_result.count or 0,
                "completed": completed_result.count or 0,
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"total": 0, "pending": 0, "completed": 0}

