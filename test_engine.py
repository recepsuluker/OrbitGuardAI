from orbit_engine import KeplerianEngine, ScientificSatellite
from skyfield.api import EarthSatellite, load, wgs84

def test_engine():
    ts = load.timescale()
    t = ts.now()
    
    # Sample TLEs (Starlink satellites, likely to be in similar orbits)
    tle1_line1 = "1 44713U 19074A   19315.45000000  .00000100  00000-0  10000-3 0  9991"
    tle1_line2 = "2 44713  53.0000 100.0000 0001000  90.0000 270.0000 15.00000000  1001"
    
    # Create a second satellite with a slightly different inclination/RAAN to force intersection
    tle2_line1 = "1 44714U 19074B   19315.45000000  .00000100  00000-0  10000-3 0  9992"
    tle2_line2 = "2 44714  53.1000 100.1000 0001000  90.0000 270.0000 15.00000000  1002"
    
    sat1 = ScientificSatellite(EarthSatellite(tle1_line1, tle1_line2, 'SAT1', ts))
    sat2 = ScientificSatellite(EarthSatellite(tle2_line1, tle2_line2, 'SAT2', ts))
    
    engine = KeplerianEngine(tolerance_km=50.0) # Large tolerance for testing
    
    print("Calculating conjunction nodes...")
    nodes = engine.calculate_conjunction_nodes(sat1, sat2, t)
    
    print(f"Found {len(nodes)} nodes.")
    for i, node in enumerate(nodes):
        print(f"Node {i+1}:")
        print(f"  Lat/Lon: {node['lat']:.2f}, {node['lon']:.2f}")
        print(f"  Distance Diff: {node['distance_diff_km']:.4f} km")
        print(f"  Frequency (f_nc): {node['f_nc']:.4f}")
        print(f"  Common Period (Tc): {node['T_c_days']:.4f} days")

    print("\nCalculating Criticality Score...")
    engine.calculate_population_criticality([sat1, sat2], t)
    print(f"SAT1 Criticality: {sat1.criticality_score}")
    print(f"SAT2 Criticality: {sat2.criticality_score}")

if __name__ == "__main__":
    test_engine()
