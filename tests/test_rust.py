"""
Tests for Rust orbit_core module
Run with: pytest tests/test_rust.py
"""

import pytest

try:
    import orbit_core
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_satellite_creation():
    """Test Rust Satellite object creation."""
    sat = orbit_core.Satellite(
        norad_id=25544,
        position=[7000.0, 0.0, 0.0],
        velocity=[0.0, 7.5, 0.0]
    )
    
    assert sat.norad_id == 25544
    assert sat.position == [7000.0, 0.0, 0.0]
    assert sat.velocity == [0.0, 7.5, 0.0]


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_satellite_distance():
    """Test distance calculation between satellites."""
    sat1 = orbit_core.Satellite(
        norad_id=1,
        position=[7000.0, 0.0, 0.0],
        velocity=[0.0, 7.5, 0.0]
    )
    
    sat2 = orbit_core.Satellite(
        norad_id=2,
        position=[7010.0, 0.0, 0.0],
        velocity=[0.0, 7.5, 0.0]
    )
    
    distance = sat1.distance_to(sat2)
    assert abs(distance - 10.0) < 0.001  # Should be 10 km


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_satellite_altitude():
    """Test altitude calculation."""
    sat = orbit_core.Satellite(
        norad_id=25544,
        position=[7000.0, 0.0, 0.0],  # 7000 km from Earth center
        velocity=[0.0, 7.5, 0.0]
    )
    
    # Earth radius ~6371 km, so altitude should be ~629 km
    alt = sat.altitude()
    assert 600 < alt < 650


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_conjunction_detection():
    """Test conjunction detection."""
    satellites = [
        orbit_core.Satellite(
            norad_id=1,
            position=[7000.0, 0.0, 0.0],
            velocity=[0.0, 7.5, 0.0]
        ),
        orbit_core.Satellite(
            norad_id=2,
            position=[7005.0, 0.0, 0.0],  # 5 km away
            velocity=[0.0, 7.5, 0.0]
        ),
        orbit_core.Satellite(
            norad_id=3,
            position=[8000.0, 0.0, 0.0],  # Far away
            velocity=[0.0, 7.5, 0.0]
        ),
    ]
    
    # Find conjunctions within 10 km
    conjunctions = orbit_core.find_conjunctions(satellites, 10.0)
    
    # Should find 1 conjunction (between sat 1 and 2)
    assert len(conjunctions) == 1
    assert conjunctions[0].norad_id_1 == 1
    assert conjunctions[0].norad_id_2 == 2
    assert conjunctions[0].distance_km < 10.0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_empty_conjunction():
    """Test conjunction detection with no close approaches."""
    satellites = [
        orbit_core.Satellite(
            norad_id=1,
            position=[7000.0, 0.0, 0.0],
            velocity=[0.0, 7.5, 0.0]
        ),
        orbit_core.Satellite(
            norad_id=2,
            position=[9000.0, 0.0, 0.0],  # 2000 km away
            velocity=[0.0, 7.5, 0.0]
        ),
    ]
    
    # Find conjunctions within 10 km
    conjunctions = orbit_core.find_conjunctions(satellites, 10.0)
    
    # Should find no conjunctions
    assert len(conjunctions) == 0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_pairwise_distances():
    """Test pairwise distance matrix."""
    satellites = [
        orbit_core.Satellite(1, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        orbit_core.Satellite(2, [10.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        orbit_core.Satellite(3, [0.0, 10.0, 0.0], [0.0, 0.0, 0.0]),
    ]
    
    distances = orbit_core.pairwise_distances(satellites)
    
    assert len(distances) == 3
    assert len(distances[0]) == 3
    
    # Diagonal should be 0
    assert distances[0][0] == 0.0
    assert distances[1][1] == 0.0
    
    # Distance between sat 1 and 2 should be 10 km
    assert abs(distances[0][1] - 10.0) < 0.001
    assert abs(distances[1][0] - 10.0) < 0.001


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not installed")
def test_closest_approaches():
    """Test finding closest approach for each satellite."""
    satellites = [
        orbit_core.Satellite(1, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        orbit_core.Satellite(2, [5.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
        orbit_core.Satellite(3, [100.0, 0.0, 0.0], [0.0, 0.0, 0.0]),
    ]
    
    closest = orbit_core.find_closest_approaches(satellites)
    
    assert len(closest) == 3
    
    # Sat 1's closest should be Sat 2 (5 km)
    assert closest[0][0] == 1  # Sat 1
    assert closest[0][1] == 2  # Closest to Sat 2
    assert abs(closest[0][2] - 5.0) < 0.001


def test_rust_not_installed():
    """Test behavior when Rust engine is not available."""
    if not RUST_AVAILABLE:
        with pytest.raises(ImportError):
            import orbit_core
