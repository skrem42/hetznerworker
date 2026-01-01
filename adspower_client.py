"""
AdsPower API Client
Wrapper for AdsPower Local API to control browser profiles.
"""
import httpx
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AdsPowerClient:
    """
    Client for AdsPower Local API.
    
    API Documentation: http://local.adspower.net:50325/doc.html
    """
    
    def __init__(self, api_url: str = "http://local.adspower.net:50325"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def list_profiles(self) -> List[Dict]:
        """
        List all browser profiles.
        
        Returns:
            List of profile dictionaries with id, name, status, etc.
        """
        try:
            response = await self.client.get(f"{self.api_url}/api/v1/user/list")
            data = response.json()
            
            if data.get("code") == 0:
                profiles = data.get("data", {}).get("list", [])
                logger.info(f"Found {len(profiles)} AdsPower profiles")
                return profiles
            else:
                logger.error(f"Failed to list profiles: {data.get('msg')}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []
    
    async def start_profile(self, profile_id: str) -> Optional[Dict]:
        """
        Launch a browser profile.
        
        Args:
            profile_id: The profile user_id
            
        Returns:
            Dictionary with 'ws' (websocket endpoint) and 'debug_port' if successful
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/v1/browser/start",
                params={"user_id": profile_id}
            )
            data = response.json()
            
            if data.get("code") == 0:
                browser_data = data.get("data", {})
                logger.info(f"Started profile {profile_id} on port {browser_data.get('debug_port')}")
                return browser_data
            else:
                logger.error(f"Failed to start profile {profile_id}: {data.get('msg')}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting profile {profile_id}: {e}")
            return None
    
    async def stop_profile(self, profile_id: str) -> bool:
        """
        Close a browser profile.
        
        Args:
            profile_id: The profile user_id
            
        Returns:
            True if successful
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/v1/browser/stop",
                params={"user_id": profile_id}
            )
            data = response.json()
            
            if data.get("code") == 0:
                logger.info(f"Stopped profile {profile_id}")
                return True
            else:
                logger.warning(f"Failed to stop profile {profile_id}: {data.get('msg')}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping profile {profile_id}: {e}")
            return False
    
    async def check_status(self, profile_id: str) -> Dict:
        """
        Check if a profile is currently active.
        
        Args:
            profile_id: The profile user_id
            
        Returns:
            Dictionary with 'status' and 'debug_port' if active
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/v1/browser/active",
                params={"user_id": profile_id}
            )
            data = response.json()
            
            if data.get("code") == 0:
                return data.get("data", {})
            else:
                return {"status": "inactive"}
                
        except Exception as e:
            logger.error(f"Error checking status for {profile_id}: {e}")
            return {"status": "error"}
    
    async def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """
        Get detailed information about a profile.
        
        Args:
            profile_id: The profile user_id
            
        Returns:
            Profile information dictionary
        """
        try:
            profiles = await self.list_profiles()
            for profile in profiles:
                if profile.get("user_id") == profile_id:
                    return profile
            return None
            
        except Exception as e:
            logger.error(f"Error getting profile info for {profile_id}: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def test_adspower_connection():
    """Test AdsPower API connection."""
    async with AdsPowerClient() as client:
        profiles = await client.list_profiles()
        if profiles:
            print(f"✓ AdsPower API connected successfully")
            print(f"✓ Found {len(profiles)} profiles:")
            for p in profiles:
                print(f"  - {p.get('name')} (ID: {p.get('user_id')})")
            return True
        else:
            print("✗ Failed to connect to AdsPower API")
            print("  Make sure AdsPower is running and API is enabled")
            return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_adspower_connection())



