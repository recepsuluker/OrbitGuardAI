import time
import numpy as np
from orbit_engine import KeplerianEngine, ScientificSatellite
from skyfield.api import EarthSatellite, load

def create_dummy_satellite(i, a, e, inc):
    # Create a dummy satellite with specific elements
    # We construct TLEs or just mock the object
    # For ScientificSatellite, we can just set the elements directly if we hack it, 
    # but better to use TLEs to be safe.
    # Actually, ScientificSatellite calculates elements from Skyfield object.
    # Let's mock the class for testing logic.
    
    class MockSat:
        def __init__(self, i, a, e):
            self.name = f"SAT_{i}"
            self.orbital_elements = {
                'a': a,
                'e': e,
                'i': inc,
                'om': 0,
                'w': 0,
                'v': 0,
                'n': 0.06 # dummy
            }
        def calculate_elements(self, t):
            return self.orbital_elements

    return MockSat(i, a, e)

def test_vectorized_filter():
    print("Generating dummy population...")
    n = 1000
    sats = []
    np.random.seed(42)
    
    # Generate random LEO orbits
    # a between 6700 and 7500 km
    # e between 0 and 0.1
    for i in range(n):
        a = np.random.uniform(6700, 7500)
        e = np.random.uniform(0, 0.1)
        sats.append(create_dummy_satellite(i, a, e, 0.5))
        
    engine = KeplerianEngine(tolerance_km=10.0)
    t = load.timescale().now()
    
    print(f"Testing with {n} satellites...")
    
    # Measure Naive Approach (conceptually)
    # We won't run full N^2 intersection check, just the filter logic check
    start = time.time()
    naive_pairs = 0
    # Naive loop for comparison
    for i in range(n):
        r1_p = sats[i].orbital_elements['a'] * (1 - sats[i].orbital_elements['e'])
        r1_a = sats[i].orbital_elements['a'] * (1 + sats[i].orbital_elements['e'])
        for j in range(i+1, n):
            r2_p = sats[j].orbital_elements['a'] * (1 - sats[j].orbital_elements['e'])
            r2_a = sats[j].orbital_elements['a'] * (1 + sats[j].orbital_elements['e'])
            if max(r1_p, r2_p) <= min(r1_a, r2_a) + 10.0:
                naive_pairs += 1
    end = time.time()
    print(f"Naive Filter Time: {end - start:.4f}s. Pairs: {naive_pairs}")
    
    # Measure Vectorized Approach
    start = time.time()
    candidates = engine.vectorized_apogee_perigee_filter(sats, t)
    end = time.time()
    print(f"Vectorized Filter Time: {end - start:.4f}s. Pairs: {len(candidates)}")
    
    assert len(candidates) == naive_pairs
    print("✅ Counts match!")

if __name__ == "__main__":
    test_vectorized_filter()
