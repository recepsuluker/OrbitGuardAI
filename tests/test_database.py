"""
Tests for database_manager.py
Run with: pytest tests/test_database.py
"""

import pytest
import os
from database_manager import DatabaseManager


@pytest.fixture
def test_db():
    """Fixture to create a test database"""
    db_path = "test_db.sqlite"
    db = DatabaseManager(db_path)
    yield db
    db.close()
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_database_initialization(test_db):
    """Test database initialization"""
    assert test_db.conn is not None
    stats = test_db.get_statistics()
    assert stats['total_satellites'] == 0


def test_insert_satellite(test_db):
    """Test satellite insertion"""
    sat_data = {
        'norad_id': 25544,
        'object_name': 'ISS (ZARYA)',
        'country': 'ISS',
        'object_type': 'PAYLOAD',
        'tle_line1': '1 25544U...',
        'tle_line2': '2 25544...',
        'epoch': '2024-001T00:00:00',
        'mean_motion': 15.5
    }
    
    result = test_db.insert_satellite(sat_data)
    assert result is True
    
    # Verify insertion
    retrieved = test_db.get_satellite(25544)
    assert retrieved is not None
    assert retrieved['object_name'] == 'ISS (ZARYA)'


def test_search_satellites(test_db):
    """Test satellite search"""
    # Insert test data
    test_db.insert_satellite({
        'norad_id': 25544,
        'object_name': 'ISS (ZARYA)',
        'tle_line1': '1',
        'tle_line2': '2',
        'epoch': '2024-001'
    })
    
    # Search by query
    results = test_db.search_satellites(query='ISS')
    assert len(results) > 0
    assert results[0]['object_name'] == 'ISS (ZARYA)'


def test_get_statistics(test_db):
    """Test statistics retrieval"""
    # Insert test satellite
    test_db.insert_satellite({
        'norad_id': 12345,
        'object_name': 'TEST SAT',
        'tle_line1': '1',
        'tle_line2': '2',
        'epoch': '2024-001'
    })
    
    stats = test_db.get_statistics()
    assert stats['total_satellites'] == 1
    assert stats['active_satellites'] == 1


def test_bulk_insert(test_db):
    """Test bulk insertion"""
    satellites = [
        {
            'norad_id': i,
            'object_name': f'SAT-{i}',
            'tle_line1': f'1 {i}U...',
            'tle_line2': f'2 {i}...',
            'epoch': '2024-001'
        }
        for i in range(1, 11)
    ]
    
    success, failed = test_db.bulk_insert(satellites)
    assert success == 10
    assert failed == 0
    
    stats = test_db.get_statistics()
    assert stats['total_satellites'] == 10
