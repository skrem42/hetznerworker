"""
LLM-based Subreddit Analysis
Uses OpenAI GPT-4o-mini to analyze subreddit rules and content.
"""
import os
import json
import logging
import asyncio
import random
import httpx
from typing import Optional
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, CRAWLER_PROXY
from user_agents import get_reddit_headers, get_reddit_cookies

logger = logging.getLogger(__name__)


class SubredditLLMAnalyzer:
    """Analyzes subreddit data using LLM to extract structured metadata."""
    
    def __init__(self, api_key: Optional[str] = None, reddit_proxy: Optional[str] = None):
        # OpenAI API key
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        # OpenAI client - NO PROXY (direct connection)
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        
        # ProxyEmpire mobile proxy for Reddit API calls
        self.reddit_proxy = reddit_proxy or CRAWLER_PROXY
        logger.info(f"LLM Analyzer initialized with ProxyEmpire mobile proxy")
    
    async def _fetch_subreddit_info(self, subreddit_name: str) -> dict:
        """Fetch subreddit info and rules from Reddit JSON API."""
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        
        # Try with retries
        for attempt in range(3):
            try:
                # Get fresh user agent and headers for each attempt
                headers = get_reddit_headers()
                cookies = get_reddit_cookies()
                
                async with httpx.AsyncClient(
                    proxy=self.reddit_proxy,
                    timeout=15.0,
                    verify=False,
                    cookies=cookies
                ) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        sub_data = data.get("data", {})
                        
                        # Extract rules
                        rules = []
                        if "community_rules" in sub_data:
                            for rule in sub_data["community_rules"]:
                                rules.append({
                                    "short_name": rule.get("short_name", ""),
                                    "description": rule.get("description", "")
                                })
                        
                        return {
                            "description": sub_data.get("public_description", ""),
                            "rules": rules,
                        }
                    
                    elif response.status_code in [403, 429]:
                        # Retry with different user agent (happens automatically on next attempt)
                        logger.warning(f"HTTP {response.status_code} for r/{subreddit_name}, retrying with new user agent...")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        await asyncio.sleep(1)
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed for r/{subreddit_name}: {e}")
                await asyncio.sleep(2 ** attempt)
        
        return {"description": "", "rules": []}

    async def analyze_subreddit(
        self,
        subreddit_name: str,
        description: str = None,
        rules: list = None,
        subscribers: int = 0,
        check_posts: bool = False,
    ) -> dict:
        """
        Analyze subreddit using LLM.
        
        Returns dict with:
        - verification_required: bool
        - sellers_allowed: str ('allowed', 'not_allowed', 'unknown')
        - niche_categories: list of strings
        - confidence: str ('high', 'medium', 'low')
        - reasoning: str
        """
        try:
            # Fetch info from Reddit if not provided
            if not description or not rules:
                logger.info(f"Fetching subreddit info for r/{subreddit_name}...")
                info = await self._fetch_subreddit_info(subreddit_name)
                description = description or info.get("description", "")
                rules = rules or info.get("rules", [])
            
            # Build rules text
            rules_text = "\n".join([
                f"- {rule.get('short_name', 'Rule')}: {rule.get('description', '')}"
                for rule in rules
            ]) if rules else "No rules provided"
            
            # Create prompt
            prompt = self._build_prompt(subreddit_name, description, rules_text, subscribers)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing NSFW subreddit rules and policies. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM analyzed r/{subreddit_name}: {result.get('confidence', 'unknown')} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis error for r/{subreddit_name}: {e}")
            return self._get_fallback_result()
    
    def _build_prompt(self, subreddit_name: str, description: str, rules_text: str, subscribers: int) -> str:
        """Build the analysis prompt."""
        subs_str = f"{subscribers:,}" if subscribers else "Unknown"
        
        return f"""Analyze this NSFW subreddit and extract key information:

**Subreddit:** r/{subreddit_name}
**Subscribers:** {subs_str}
**Description:** {description or "No description"}

**Rules:**
{rules_text}

Determine:

1. **Verification Required**: Does this subreddit require users to verify their identity?

2. **Sellers Allowed**: Are OnlyFans creators, sellers, or self-promotion allowed?
   - Return "allowed" if creators/sellers are explicitly welcome OR no restrictions mentioned
   - Return "not_allowed" if there are explicit bans on OnlyFans, sellers, or "amateur only" rules
   - Return "unknown" if unclear

3. **Niche Categories**: Main content themes (e.g., amateur, petite, asian, milf, etc.)

4. **Confidence**: How confident are you? (high/medium/low)

Return JSON:
{{
  "verification_required": true or false,
  "sellers_allowed": "allowed" or "not_allowed" or "unknown",
  "niche_categories": ["category1", "category2"],
  "confidence": "high" or "medium" or "low",
  "reasoning": "Brief explanation"
}}"""
    
    def _get_fallback_result(self) -> dict:
        """Return fallback result if LLM analysis fails."""
        return {
            "verification_required": False,
            "sellers_allowed": "unknown",
            "niche_categories": ["unknown"],
            "confidence": "low",
            "reasoning": "Analysis failed - using fallback defaults"
        }

