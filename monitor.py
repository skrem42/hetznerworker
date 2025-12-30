#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard
Shows live stats for both workers.
"""
import asyncio
import sys
from datetime import datetime, timezone
from supabase_client import SupabaseClient
from adspower_client import AdsPowerClient
from config import ADSPOWER_PROFILE_IDS, MONITOR_REFRESH_SECONDS


class Monitor:
    """Real-time monitoring dashboard."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.adspower = AdsPowerClient()
        self.metrics_file = "logs/monitor_history.json"
    
    def load_history(self):
        """Load historical metrics for growth calculations."""
        import json
        import os
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_history(self, current_metrics):
        """Save current metrics to history."""
        import json
        import os
        try:
            history = self.load_history()
            
            # Add current metrics with timestamp
            history.append(current_metrics)
            
            # Keep only last 168 data points (7 days at 1 hour intervals)
            history = history[-168:]
            
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            
            with open(self.metrics_file, 'w') as f:
                json.dump(history, f)
        except Exception as e:
            pass  # Silent fail - not critical
    
    async def get_browser_status(self):
        """Check status of AdsPower browsers."""
        active_count = 0
        total_count = len([p for p in ADSPOWER_PROFILE_IDS if not p.startswith("PROFILE_")])
        
        try:
            for profile_id in ADSPOWER_PROFILE_IDS:
                if profile_id.startswith("PROFILE_"):
                    continue
                
                status = await self.adspower.check_status(profile_id)
                if status.get("status") == "Active":
                    active_count += 1
        except:
            pass
        
        return active_count, total_count
    
    async def display_dashboard(self):
        """Display the monitoring dashboard."""
        from datetime import timedelta
        
        # Get database stats
        queue_stats = await self.supabase.get_queue_stats()
        intel_stats = await self.supabase.get_intel_stats()
        
        # Get browser status
        browsers_active, browsers_total = await self.get_browser_status()
        
        # Time windows for analysis
        now = datetime.now(timezone.utc)
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        six_hours_ago = (now - timedelta(hours=6)).isoformat()
        twenty_four_hours_ago = (now - timedelta(hours=24)).isoformat()
        
        # Recent scraping activity
        try:
            recent_1h = self.supabase.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "completed").gte("last_scraped_at", one_hour_ago).execute()
            recent_1h_count = recent_1h.count or 0
        except:
            recent_1h_count = 0
        
        try:
            recent_6h = self.supabase.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "completed").gte("last_scraped_at", six_hours_ago).execute()
            recent_6h_count = recent_6h.count or 0
        except:
            recent_6h_count = 0
        
        try:
            recent_24h = self.supabase.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "completed").gte("last_scraped_at", twenty_four_hours_ago).execute()
            recent_24h_count = recent_24h.count or 0
        except:
            recent_24h_count = 0
        
        # Recent discovery activity (queue growth)
        try:
            # Get new discoveries in last hour  
            # This counts how many subs were added to queue recently
            recent_discovered_1h = self.supabase.client.table("subreddit_queue").select(
                "*", count="exact", head=True
            ).gte("created_at", one_hour_ago).execute() if hasattr(self.supabase.client.table("subreddit_queue"), "created_at") else None
            
            # Fallback: estimate from queue size changes
            current_queue_size = queue_stats["total"]
        except:
            recent_discovered_1h = None
            current_queue_size = queue_stats["total"]
        
        # Calculate rates
        rate_1h = recent_1h_count
        rate_6h = recent_6h_count / 6 if recent_6h_count > 0 else 0
        rate_24h = recent_24h_count / 24 if recent_24h_count > 0 else 0
        
        # Use best available rate (prefer recent)
        current_rate = rate_1h if rate_1h > 0 else (rate_6h if rate_6h > 0 else rate_24h)
        
        # Calculate percentages and estimates
        queue_total = queue_stats["total"]
        queue_pending = queue_stats["pending"]
        queue_completed = queue_stats["completed"]
        queue_completion_pct = (queue_completed / queue_total * 100) if queue_total > 0 else 0
        
        intel_total = intel_stats["total"]
        intel_completed = intel_stats["completed"]
        intel_pending = intel_stats.get("pending", 0)
        intel_failed = intel_stats.get("failed", 0)
        
        # Items left to scrape
        items_remaining = intel_pending + intel_failed + (queue_total - intel_total)
        
        # Time estimates
        if current_rate > 0:
            hours_to_completion = items_remaining / current_rate
            days_to_completion = hours_to_completion / 24
        else:
            hours_to_completion = 0
            days_to_completion = 0
        
        # Clear screen
        print("\033[2J\033[H", end="")
        
        # Display dashboard
        print("="*80)
        print(" " * 22 + "🚀 HETZNER WORKER DASHBOARD")
        print("="*80)
        print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print()
        
        # System Status
        print("="*80)
        print("📱 SYSTEM STATUS")
        print("="*80)
        if browsers_active > 0:
            status_icon = "🟢" if browsers_active == browsers_total else "🟡"
            status_text = "Running" if browsers_active == browsers_total else "Partial"
        else:
            status_icon = "🔴"
            status_text = "Stopped"
        print(f"  Intel Worker:        {status_icon} {status_text} ({browsers_active}/{browsers_total} browsers)")
        print(f"  Crawler:             🟢 Active (discovering new subs)")
        print()
        
        # Performance Metrics
        print("="*80)
        print("⚡ PERFORMANCE (Intel Worker Scraping)")
        print("="*80)
        print(f"  Last Hour:           {rate_1h:,.1f} subs/hour ({recent_1h_count} successfully scraped)")
        print(f"  Last 6 Hours:        {rate_6h:,.1f} subs/hour (avg)")
        print(f"  Last 24 Hours:       {rate_24h:,.1f} subs/hour (avg)")
        print(f"  Current Rate:        {current_rate:,.1f} subs/hour")
        if current_rate > 0:
            print(f"  Est. Daily Output:   {current_rate * 24:,.0f} subs/day (successful only)")
        print(f"  Note: Rate = completed scrapes (excludes retries/failures)")
        print()
        
        # Progress & ETA
        print("="*80)
        print("📊 PROGRESS & ETA")
        print("="*80)
        completion_pct = (intel_completed / queue_total * 100) if queue_total > 0 else 0
        print(f"  Total Subs in Queue: {queue_total:,}")
        print(f"  Completed:           {intel_completed:,} ({completion_pct:.1f}%)")
        print(f"  Pending:             {intel_pending:,}")
        print(f"  Failed (retrying):   {intel_failed:,}")
        print(f"  Not Started:         {queue_total - intel_total:,}")
        print(f"  ────────────────────────────────")
        print(f"  Remaining:           {items_remaining:,} subs")
        if hours_to_completion > 0:
            if days_to_completion < 1:
                print(f"  Est. Completion:     {hours_to_completion:.1f} hours")
            elif days_to_completion < 7:
                print(f"  Est. Completion:     {days_to_completion:.1f} days")
            else:
                weeks = days_to_completion / 7
                print(f"  Est. Completion:     {weeks:.1f} weeks")
        else:
            print(f"  Est. Completion:     Calculating...")
        print()
        
        # Discovery Stats - Calculate from historical data
        print("="*80)
        print("🔍 DISCOVERY (Crawler)")
        print("="*80)
        print(f"  Total in Queue:      {queue_total:,} subs")
        
        # Calculate backlog
        not_yet_scraped = queue_total - intel_total
        print(f"  Not Yet Scraped:     {not_yet_scraped:,} subs")
        
        # Load historical data to calculate actual growth
        history = self.load_history()
        
        # Calculate real discovery rate from historical data
        discovery_rate_hourly = None
        if len(history) >= 2:
            # Find data from 1 hour ago
            for i in range(len(history) - 1, -1, -1):
                time_diff = (now - datetime.fromisoformat(history[i]["timestamp"])).total_seconds() / 3600
                if 0.8 <= time_diff <= 1.2:  # Around 1 hour ago
                    queue_growth = queue_total - history[i]["queue_total"]
                    intel_growth = intel_completed - history[i]["intel_completed"]
                    # Net queue growth = new discoveries - scrapes
                    discovery_rate_hourly = queue_growth + intel_growth
                    break
        
        # Save current metrics to history
        current_metrics = {
            "timestamp": now.isoformat(),
            "queue_total": queue_total,
            "intel_completed": intel_completed,
            "intel_total": intel_total
        }
        self.save_history(current_metrics)
        
        # Display discovery metrics
        scraping_rate_daily = current_rate * 24 if current_rate > 0 else 0
        print(f"  Scraping Rate:       {scraping_rate_daily:,.0f} subs/day")
        
        if discovery_rate_hourly is not None:
            daily_discovery = discovery_rate_hourly * 24
            print(f"  Discovery Rate:      {discovery_rate_hourly:,.1f} subs/hour (measured)")
            print(f"  Daily Discovery:     {daily_discovery:,.0f} subs/day (measured)")
            
            # Net growth
            net_daily = daily_discovery - scraping_rate_daily
            if net_daily > 0:
                print(f"  Net Queue Growth:    +{net_daily:,.0f} subs/day (growing)")
            else:
                print(f"  Net Queue Growth:    {net_daily:,.0f} subs/day (shrinking)")
        else:
            print(f"  Discovery Rate:      Tracking... (need 1 hour of data)")
            print(f"  Daily Discovery:     Calculating...")
        
        print(f"  Coverage Goal:       Complete NSFW catalog (ongoing)")
        print()
        
        # Health Check
        print("="*80)
        print("🏥 HEALTH & DIAGNOSTICS")
        print("="*80)
        success_rate = (intel_completed / intel_total * 100) if intel_total > 0 else 0
        retry_rate = ((intel_pending + intel_failed) / intel_total * 100) if intel_total > 0 else 0
        print(f"  Success Rate:        {success_rate:.1f}% ({intel_completed:,}/{intel_total:,})")
        print(f"  Pending Retry:       {intel_pending:,} subs")
        print(f"  Failed (retrying):   {intel_failed:,} subs")
        print(f"  Overall Retry Rate:  {retry_rate:.1f}%")
        
        # Provide context for high retry rate
        if retry_rate > 30:
            print(f"  Status:              ⚠️  High retry rate")
            if intel_failed > intel_pending:
                print(f"  Diagnosis:           Mostly old failures (will retry now)")
            else:
                print(f"  Diagnosis:           Many recent failures - check logs for issues")
        elif retry_rate > 15:
            print(f"  Status:              🟡 Moderate retry rate")
        else:
            print(f"  Status:              🟢 Healthy")
        
        # Recent activity health
        if current_rate > 0:
            recent_success = (recent_1h_count / (recent_1h_count + intel_pending) * 100) if (recent_1h_count + intel_pending) > 0 else 100
            print(f"  Recent Success:      {recent_success:.1f}% (last hour)")
        print()
        
        # Footer
        print("="*80)
        print("Press Ctrl+C to exit")
        print(f"Refreshing every {MONITOR_REFRESH_SECONDS} seconds...")
        print("="*80)
    
    async def run(self):
        """Main monitoring loop."""
        try:
            while True:
                await self.display_dashboard()
                await asyncio.sleep(MONITOR_REFRESH_SECONDS)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
        finally:
            await self.adspower.close()


async def main():
    """Entry point."""
    monitor = Monitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())

