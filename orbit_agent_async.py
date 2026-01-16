"""
Async Orbit Agent - Concurrent TLE fetching from Space-Track.org
Provides 5-10x speedup for multi-satellite analysis
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AsyncOrbitAgent:
    """
    Asynchronous satellite tracking agent for parallel data fetching.
    
    Features:
    - Concurrent TLE fetching for multiple satellites
    - Automatic session management
    - Error handling and retry logic
    - Rate limiting support
    """
    
    def __init__(self, username: str, password: str, timeout: int = 30):
        """
        Initialize async agent.
        
        Args:
            username: Space-Track.org username
            password: Space-Track.org password
            timeout: Request timeout in seconds
        """
        self.username = username
        self.password = password
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://www.space-track.org"
    
    async def __aenter__(self):
        """Context manager entry - create session."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        await self._login()
        return self
    
    async def __aexit__(self, *args):
        """Context manager exit - close session."""
        if self.session:
            await self.session.close()
    
    async def _login(self):
        """
        Authenticate with Space-Track.org.
        Required before making API requests.
        """
        login_url = f"{self.base_url}/ajaxauth/login"
        login_data = {
            'identity': self.username,
            'password': self.password
        }
        
        try:
            async with self.session.post(login_url, data=login_data) as resp:
                if resp.status == 200:
                    logger.info("✅ Space-Track authentication successful")
                else:
                    raise Exception(f"Login failed with status {resp.status}")
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise
    
    async def fetch_single_tle(self, norad_id: int, retries: int = 3) -> Optional[Dict]:
        """
        Fetch TLE for a single satellite.
        
        Args:
            norad_id: NORAD catalog ID
            retries: Number of retry attempts
            
        Returns:
            TLE data dict or None on failure
        """
        url = (f"{self.base_url}/basicspacedata/query/class/tle_latest/"
               f"NORAD_CAT_ID/{norad_id}/format/json")
        
        for attempt in range(retries):
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and len(data) > 0:
                            logger.debug(f"✅ Fetched TLE for {norad_id}")
                            return data[0]
                        else:
                            logger.warning(f"⚠️  No TLE data for {norad_id}")
                            return None
                    else:
                        logger.warning(f"⚠️  HTTP {resp.status} for {norad_id}")
            except Exception as e:
                logger.error(f"❌ Error fetching {norad_id} (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
        
        return None
    
    async def fetch_batch_tle(self, norad_ids: List[int]) -> Dict[int, Dict]:
        """
        Fetch TLE data for multiple satellites concurrently.
        
        Args:
            norad_ids: List of NORAD catalog IDs
            
        Returns:
            Dict mapping NORAD ID to TLE data
        """
        logger.info(f"📡 Fetching TLE for {len(norad_ids)} satellites (async)...")
        start_time = datetime.now()
        
        # Create concurrent tasks
        tasks = [self.fetch_single_tle(nid) for nid in norad_ids]
        results = await asyncio.gather(*tasks)
        
        # Build result dictionary
        tle_dict = {}
        for norad_id, tle_data in zip(norad_ids, results):
            if tle_data:
                tle_dict[norad_id] = tle_data
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Fetched {len(tle_dict)}/{len(norad_ids)} satellites in {elapsed:.2f}s")
        
        return tle_dict
    
    async def fetch_batch_with_semaphore(self, norad_ids: List[int], 
                                        max_concurrent: int = 10) -> Dict[int, Dict]:
        """
        Fetch TLE data with concurrency limit.
        
        Args:
            norad_ids: List of NORAD catalog IDs
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dict mapping NORAD ID to TLE data
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_sem(norad_id):
            async with semaphore:
                return await self.fetch_single_tle(norad_id)
        
        logger.info(f"📡 Fetching {len(norad_ids)} satellites (max {max_concurrent} concurrent)...")
        start_time = datetime.now()
        
        tasks = [fetch_with_sem(nid) for nid in norad_ids]
        results = await asyncio.gather(*tasks)
        
        tle_dict = {}
        for norad_id, tle_data in zip(norad_ids, results):
            if tle_data:
                tle_dict[norad_id] = tle_data
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Fetched {len(tle_dict)}/{len(norad_ids)} satellites in {elapsed:.2f}s")
        
        return tle_dict


def run_sync(norad_ids: List[int], username: str, password: str) -> Dict[int, Dict]:
    """
    Synchronous wrapper for async TLE fetching.
    Use this from non-async code (e.g., Streamlit).
    
    Args:
        norad_ids: List of NORAD catalog IDs
        username: Space-Track.org username
        password: Space-Track.org password
        
    Returns:
        Dict mapping NORAD ID to TLE data
    """
    async def _fetch():
        async with AsyncOrbitAgent(username, password) as agent:
            return await agent.fetch_batch_tle(norad_ids)
    
    # Create new event loop for sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_fetch())
    finally:
        loop.close()


if __name__ == "__main__":
    # Test the async agent
    logging.basicConfig(level=logging.INFO)
    
    # Test credentials (replace with real ones)
    USERNAME = "your_username"
    PASSWORD = "your_password"
    
    # Test NORAD IDs (ISS, Starlink satellites)
    test_ids = [25544, 48274, 52740, 55012, 56210]
    
    async def test_async():
        async with AsyncOrbitAgent(USERNAME, PASSWORD) as agent:
            tle_data = await agent.fetch_batch_tle(test_ids)
            print(f"\nFetched {len(tle_data)} satellites:")
            for norad_id, data in tle_data.items():
                print(f"  - {norad_id}: {data.get('OBJECT_NAME', 'Unknown')}")
    
    # Run test
    print("Testing async agent...")
    # asyncio.run(test_async())  # Uncomment with real credentials
    
    # Test sync wrapper
    print("\nTesting sync wrapper...")
    # results = run_sync(test_ids, USERNAME, PASSWORD)  # Uncomment with real credentials
    # print(f"Sync wrapper returned {len(results)} satellites")
