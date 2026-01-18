"""
Database Manager for OrbitGuard AI
Handles SQLite database for TLE catalog storage and queries
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite database manager for satellite TLE data.
    
    Features:
    - Automatic schema creation
    - TLE storage and retrieval
    - Search and filtering
    - Indexing for performance
    """
    
    def __init__(self, db_path: str = "orbitguard.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database and tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = self.conn.cursor()
        
        # Create satellites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS satellites (
                norad_id INTEGER PRIMARY KEY,
                object_name TEXT NOT NULL,
                intl_designator TEXT,
                country TEXT,
                object_type TEXT,
                launch_date TEXT,
                tle_line1 TEXT NOT NULL,
                tle_line2 TEXT NOT NULL,
                epoch TEXT NOT NULL,
                mean_motion REAL,
                eccentricity REAL,
                inclination REAL,
                raan REAL,
                arg_perigee REAL,
                mean_anomaly REAL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for fast querying
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_object_name 
            ON satellites(object_name)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_country 
            ON satellites(country)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_object_type 
            ON satellites(object_type)
        ''')
        
        # Create update history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_type TEXT NOT NULL,
                satellites_updated INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        self.conn.commit()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def insert_satellite(self, satellite_data: Dict) -> bool:
        """
        Insert or update satellite TLE data.
        
        Args:
            satellite_data: Dictionary with satellite information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO satellites (
                    norad_id, object_name, intl_designator, country, object_type,
                    tle_line1, tle_line2, epoch, mean_motion, eccentricity,
                    inclination, raan, arg_perigee, mean_anomaly, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                satellite_data.get('norad_id'),
                satellite_data.get('object_name', 'UNKNOWN'),
                satellite_data.get('intl_designator'),
                satellite_data.get('country'),
                satellite_data.get('object_type'),
                satellite_data.get('tle_line1'),
                satellite_data.get('tle_line2'),
                satellite_data.get('epoch'),
                satellite_data.get('mean_motion'),
                satellite_data.get('eccentricity'),
                satellite_data.get('inclination'),
                satellite_data.get('raan'),
                satellite_data.get('arg_perigee'),
                satellite_data.get('mean_anomaly'),
                datetime.utcnow().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Insert error for NORAD {satellite_data.get('norad_id')}: {e}")
            return False
    
    def bulk_insert(self, satellites: List[Dict]) -> Tuple[int, int]:
        """
        Insert multiple satellites in batch.
        
        Args:
            satellites: List of satellite data dictionaries
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        success_count = 0
        fail_count = 0
        
        for sat in satellites:
            if self.insert_satellite(sat):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"Bulk insert: {success_count} success, {fail_count} failed")
        return success_count, fail_count
    
    def get_satellite(self, norad_id: int) -> Optional[Dict]:
        """
        Get satellite by NORAD ID.
        
        Args:
            norad_id: NORAD catalog ID
            
        Returns:
            Satellite data dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM satellites WHERE norad_id = ?', (norad_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def search_satellites(
        self,
        query: Optional[str] = None,
        country: Optional[str] = None,
        object_type: Optional[str] = None,
        orbit_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Search satellites with advanced filters.
        
        Args:
            query: Search term (name or NORAD ID)
            country: Filter by country
            object_type: Filter by object type (PAYLOAD, DEBRIS, etc.)
            orbit_type: LEO, MEO, GEO, HEO
            status: Active, Inactive
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of satellite dictionaries
        """
        cursor = self.conn.cursor()
        
        # Build dynamic query
        sql = 'SELECT * FROM satellites WHERE 1=1'
        params = []
        
        if query:
            # Check if query is numeric (NORAD ID)
            if query.isdigit():
                sql += ' AND norad_id = ?'
                params.append(int(query))
            else:
                sql += ' AND object_name LIKE ?'
                params.append(f'%{query}%')
        
        if country and country != "All":
            sql += ' AND country = ?'
            params.append(country)
        
        if object_type and object_type != "All":
            sql += ' AND object_type = ?'
            params.append(object_type)
            
        if status:
            if status == "Active":
                # Definition of active: is_active=1 AND epoch within last 30 days
                thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                sql += ' AND is_active = 1 AND epoch > ?'
                params.append(thirty_days_ago)
            elif status == "Inactive":
                sql += ' AND is_active = 0'
        
        if orbit_type:
            # Mean Motion thresholds:
            # LEO: > 11.25 rad/day (period < 128 min)
            # GEO: ~ 1.0027 rad/day (period ~ 24h)
            # MEO: 1.0027 < MM < 11.25
            if orbit_type == "LEO":
                sql += ' AND mean_motion > 11.25'
            elif orbit_type == "GEO":
                sql += ' AND mean_motion >= 0.99 AND mean_motion <= 1.01 AND eccentricity < 0.01'
            elif orbit_type == "MEO":
                sql += ' AND mean_motion > 1.01 AND mean_motion <= 11.25'
            elif orbit_type == "HEO":
                sql += ' AND eccentricity > 0.5'
        
        sql += ' ORDER BY object_name LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        # Apply fuzzy search if query is provided and it's not a NORAD ID
        if query and not query.isdigit():
            try:
                from thefuzz import process
                # Extract names for fuzzy matching
                names = [r['object_name'] for r in results]
                fuzzy_matches = process.extract(query, names, limit=limit)
                
                # Rebuild results based on fuzzy scores
                # Only keep matches with a decent score (>60)
                filtered_results = []
                # Map names back to objects
                name_map = {r['object_name']: r for r in results}
                
                for name, score in fuzzy_matches:
                    if score > 60:
                        filtered_results.append(name_map[name])
                
                return filtered_results
                
            except ImportError:
                # Fallback to standard results if thefuzz is not installed
                logger.warning("thefuzz not found, using SQL LIKE results")
                return results
                
        return results
    
    def get_all_norad_ids(self) -> List[int]:
        """Get list of all NORAD IDs in database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT norad_id FROM satellites ORDER BY norad_id')
        return [row[0] for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        # Total satellites
        cursor.execute('SELECT COUNT(*) FROM satellites')
        total_sats = cursor.fetchone()[0]
        
        # Active satellites
        cursor.execute('SELECT COUNT(*) FROM satellites WHERE is_active = 1')
        active_sats = cursor.fetchone()[0]
        
        # By country
        cursor.execute('''
            SELECT country, COUNT(*) as count 
            FROM satellites 
            WHERE country IS NOT NULL 
            GROUP BY country 
            ORDER BY count DESC
        ''')
        top_countries = [dict(row) for row in cursor.fetchall()]
        
        # By object type
        cursor.execute('''
            SELECT object_type, COUNT(*) as count 
            FROM satellites 
            WHERE object_type IS NOT NULL 
            GROUP BY object_type 
            ORDER BY count DESC
        ''')
        object_types = [dict(row) for row in cursor.fetchall()]
        
        # Last update
        cursor.execute('SELECT MAX(updated_at) FROM satellites')
        last_update = cursor.fetchone()[0]
        
        return {
            'total_satellites': total_sats,
            'active_satellites': active_sats,
            'inactive_satellites': total_sats - active_sats,
            'top_countries': top_countries,
            'object_types': object_types,
            'last_update': last_update,
            'database_path': self.db_path
        }
    
    def log_update(self, update_type: str, count: int, status: str, error: Optional[str] = None):
        """
        Log catalog update to history.
        
        Args:
            update_type: Type of update (e.g., "full_sync", "incremental")
            count: Number of satellites updated
            status: "success" or "failed"
            error: Error message if failed
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO update_history (update_type, satellites_updated, status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (update_type, count, status, error))
        self.conn.commit()
    
    def get_update_history(self, limit: int = 10) -> List[Dict]:
        """Get recent update history."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM update_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Test the database manager
    logging.basicConfig(level=logging.INFO)
    
    db = DatabaseManager("test_orbitguard.db")
    
    # Insert test satellite
    test_sat = {
        'norad_id': 25544,
        'object_name': 'ISS (ZARYA)',
        'country': 'ISS',
        'object_type': 'PAYLOAD',
        'tle_line1': '1 25544U 98067A   21001.00000000  .00000000  00000-0  00000-0 0  0000',
        'tle_line2': '2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.48919393000000',
        'epoch': '2021-001T00:00:00',
        'mean_motion': 15.48919393,
        'inclination': 51.6416
    }
    
    db.insert_satellite(test_sat)
    
    # Search
    results = db.search_satellites(query='ISS')
    print(f"Search results: {len(results)}")
    
    # Stats
    stats = db.get_statistics()
    print(f"Database stats: {stats}")
    
    db.close()
