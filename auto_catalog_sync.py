"""
Auto Catalog Sync - Automatic TLE database synchronization
Periodically fetches full satellite catalog from Space-Track.org
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Optional
import logging

from database_manager import DatabaseManager
from orbit_agent_async import AsyncOrbitAgent
from cache_manager import TLECacheManager

logger = logging.getLogger(__name__)


class AutoCatalogSync:
    """
    Automatic catalog synchronization system.
    
    Features:
    - Scheduled TLE updates (default: every 24 hours)
    - Full catalog fetch from Space-Track.org
    - Database storage
    - Cache integration
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        username: str,
        password: str,
        update_interval_hours: int = 24,
        db_path: str = "orbitguard.db"
    ):
        """
        Initialize auto-sync system.
        
        Args:
            username: Space-Track.org username
            password: Space-Track.org password
            update_interval_hours: Update frequency in hours
            db_path: Database file path
        """
        self.username = username
        self.password = password
        self.update_interval = update_interval_hours
        self.db = DatabaseManager(db_path)
        self.cache = TLECacheManager()
        self.is_running = False
        self.last_sync: Optional[datetime] = None
    
    async def fetch_full_catalog(self) -> int:
        """
        Fetch complete satellite catalog from Space-Track.org.
        
        Returns:
            Number of satellites fetched
        """
        logger.info("📡 Starting full catalog fetch from Space-Track.org...")
        
        try:
            async with AsyncOrbitAgent(self.username, self.password) as agent:
                # Fetch latest TLEs for all satellites
                # Space-Track API endpoint for full catalog
                url = f"{agent.base_url}/basicspacedata/query/class/tle_latest/ORDINAL/1/format/json"
                
                async with agent.session.get(url) as resp:
                    if resp.status == 200:
                        catalog = await resp.json()
                        logger.info(f"✅ Fetched {len(catalog)} satellites from API")
                        return catalog
                    else:
                        logger.error(f"API error: HTTP {resp.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Catalog fetch error: {e}")
            return []
    
    async def sync_catalog(self) -> bool:
        """
        Synchronize catalog to database.
        
        Returns:
            True if successful, False otherwise
        """
        start_time = datetime.utcnow()
        logger.info(f"🔄 Starting catalog sync at {start_time.isoformat()}")
        
        try:
            # Fetch catalog
            catalog = await self.fetch_full_catalog()
            
            if not catalog:
                logger.warning("No data fetched - aborting sync")
                self.db.log_update("full_sync", 0, "failed", "No data from API")
                return False
            
            # Process and insert satellites
            satellites_to_insert = []
            
            for tle_entry in catalog:
                sat_data = {
                    'norad_id': int(tle_entry.get('NORAD_CAT_ID', 0)),
                    'object_name': tle_entry.get('OBJECT_NAME', 'UNKNOWN'),
                    'intl_designator': tle_entry.get('OBJECT_ID'),
                    'country': tle_entry.get('COUNTRY_CODE'),
                    'object_type': tle_entry.get('OBJECT_TYPE'),
                    'tle_line1': tle_entry.get('TLE_LINE1'),
                    'tle_line2': tle_entry.get('TLE_LINE2'),
                    'epoch': tle_entry.get('EPOCH'),
                    'mean_motion': float(tle_entry.get('MEAN_MOTION', 0)),
                    'eccentricity': float(tle_entry.get('ECCENTRICITY', 0)),
                    'inclination': float(tle_entry.get('INCLINATION', 0)),
                    'raan': float(tle_entry.get('RA_OF_ASC_NODE', 0)),
                    'arg_perigee': float(tle_entry.get('ARG_OF_PERICENTER', 0)),
                    'mean_anomaly': float(tle_entry.get('MEAN_ANOMALY', 0))
                }
                satellites_to_insert.append(sat_data)
            
            # Bulk insert
            success_count, fail_count = self.db.bulk_insert(satellites_to_insert)
            
            # Update sync status
            self.last_sync = datetime.utcnow()
            elapsed = (self.last_sync - start_time).total_seconds()
            
            logger.info(f"✅ Sync completed in {elapsed:.1f}s")
            logger.info(f"   - Successful: {success_count}")
            logger.info(f"   - Failed: {fail_count}")
            
            # Log to database
            self.db.log_update("full_sync", success_count, "success")
            
            # Invalidate cache (new data available)
            self.cache.invalidate_all()
            
            return True
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            self.db.log_update("full_sync", 0, "failed", str(e))
            return False
    
    def schedule_sync(self):
        """
        Schedule periodic catalog synchronization.
        Uses schedule library for recurring tasks.
        """
        logger.info(f"⏰ Scheduling catalog sync every {self.update_interval} hours")
        
        # Schedule first sync immediately
        schedule.every(self.update_interval).hours.do(self._run_sync_job)
        
        # Also run once at startup
        self._run_sync_job()
    
    def _run_sync_job(self):
        """Run sync job (wrapper for asyncio)."""
        logger.info("🔄 Scheduled sync job triggered")
        
        # Run async sync in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.sync_catalog())
            if result:
                logger.info("✅ Scheduled sync successful")
            else:
                logger.warning("⚠️  Scheduled sync failed")
        finally:
            loop.close()
    
    def start(self):
        """
        Start the auto-sync daemon.
        Runs in background and performs periodic updates.
        """
        logger.info("🚀 Starting AutoCatalogSync daemon...")
        self.is_running = True
        
        # Schedule syncs
        self.schedule_sync()
        
        # Keep running
        logger.info("✅ Daemon running. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Daemon stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the daemon."""
        self.is_running = False
        self.db.close()
        logger.info("AutoCatalogSync stopped")
    
    def get_status(self) -> dict:
        """
        Get sync status information.
        
        Returns:
            Status dictionary
        """
        db_stats = self.db.get_statistics()
        update_history = self.db.get_update_history(limit=5)
        
        return {
            'is_running': self.is_running,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'update_interval_hours': self.update_interval,
            'database': db_stats,
            'recent_updates': update_history
        }


# ============================================================================
# Standalone Script
# ============================================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get credentials
    username = os.getenv('SPACETRACK_USERNAME')
    password = os.getenv('SPACETRACK_PASSWORD')
    
    if not username or not password:
        logger.error("❌ Space-Track credentials not found in .env file")
        logger.error("   Set SPACETRACK_USERNAME and SPACETRACK_PASSWORD")
        exit(1)
    
    # Create sync daemon
    sync_daemon = AutoCatalogSync(
        username=username,
        password=password,
        update_interval_hours=24  # Daily updates
    )
    
    # Option 1: Run once (manual sync)
    print("\n🔄 Running manual sync (one-time)...")
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(sync_daemon.sync_catalog())
    
    if success:
        print("\n✅ Manual sync completed!")
        print("\n📊 Database statistics:")
        stats = sync_daemon.db.get_statistics()
        print(f"   Total satellites: {stats['total_satellites']}")
        print(f"   Active satellites: {stats['active_satellites']}")
        print(f"   Last update: {stats['last_update']}")
    
    # Option 2: Start daemon (uncomment to run continuously)
    # print("\n🚀 Starting daemon mode...")
    # sync_daemon.start()
