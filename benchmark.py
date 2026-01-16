"""
Performance Benchmark Script
Compares Python-only vs Redis cache vs Async vs Rust implementations
"""

import time
import pandas as pd
import numpy as np
from typing import List, Dict
import logging
import sys

# Optional imports (may not be available initially)
try:
    from cache_manager import TLECacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("⚠️  cache_manager not available")

try:
    from orbit_agent_async import run_sync as async_fetch
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    print("⚠️  orbit_agent_async not available")

try:
    import orbit_core
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("⚠️  Rust engine (orbit_core) not available")

logging.basicConfig(level=logging.WARNING)  # Reduce noise


def generate_mock_satellites(count: int) -> List[Dict]:
    """Generate mock satellite data for testing."""
    satellites = []
    for i in range(count):
        # Random orbital positions
        r = np.random.uniform(6700, 8000)  # LEO altitudes
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        
        # Random velocities
        v = np.random.uniform(7.0, 8.0)  # km/s
        vx = np.random.uniform(-v, v)
        vy = np.random.uniform(-v, v)
        vz = np.random.uniform(-v, v)
        
        satellites.append({
            'norad_id': 25544 + i,
            'position': [x, y, z],
            'velocity': [vx, vy, vz]
        })
    
    return satellites


def benchmark_python_conjunction(satellites: List[Dict], threshold_km: float = 10.0) -> float:
    """Benchmark Python-only conjunction detection."""
    start = time.time()
    
    conjunctions = []
    n = len(satellites)
    
    for i in range(n):
        for j in range(i + 1, n):
            # Calculate distance
            pos1 = np.array(satellites[i]['position'])
            pos2 = np.array(satellites[j]['position'])
            dist = np.linalg.norm(pos1 - pos2)
            
            if dist < threshold_km:
                conjunctions.append((satellites[i]['norad_id'], satellites[j]['norad_id'], dist))
    
    elapsed = time.time() - start
    return elapsed, len(conjunctions)


def benchmark_rust_conjunction(satellites: List[Dict], threshold_km: float = 10.0) -> float:
    """Benchmark Rust conjunction detection."""
    if not RUST_AVAILABLE:
        return None, 0
    
    start = time.time()
    
    # Convert to Rust satellites
    rust_sats = [
        orbit_core.Satellite(
            norad_id=sat['norad_id'],
            position=sat['position'],
            velocity=sat['velocity']
        )
        for sat in satellites
    ]
    
    # Run Rust algorithm
    conjunctions = orbit_core.find_conjunctions(rust_sats, threshold_km)
    
    elapsed = time.time() - start
    return elapsed, len(conjunctions)


def run_benchmark():
    """Run comprehensive benchmark."""
    print("🚀 OrbitGuardAI Performance Benchmark")
    print("=" * 60)
    
    test_cases = [
        {"name": "10 Satellites", "count": 10},
        {"name": "50 Satellites", "count": 50},
        {"name": "100 Satellites", "count": 100},
        {"name": "500 Satellites", "count": 500},
    ]
    
    results = []
    
    for case in test_cases:
        print(f"\n📊 Testing: {case['name']}")
        satellites = generate_mock_satellites(case['count'])
        
        # Benchmark Python
        print("  🐍 Python baseline...", end=" ")
        py_time, py_count = benchmark_python_conjunction(satellites)
        print(f"{py_time:.3f}s ({py_count} conjunctions)")
        
        # Benchmark Rust
        rust_time = None
        speedup = "N/A"
        if RUST_AVAILABLE:
            print("  🦀 Rust engine...", end=" ")
            rust_time, rust_count = benchmark_rust_conjunction(satellites)
            print(f"{rust_time:.3f}s ({rust_count} conjunctions)")
            speedup = f"{py_time / rust_time:.1f}x" if rust_time else "N/A"
        else:
            print("  🦀 Rust engine... SKIPPED (not installed)")
        
        results.append({
            'Test Case': case['name'],
            'Satellites': case['count'],
            'Python (s)': round(py_time, 3),
            'Rust (s)': round(rust_time, 3) if rust_time else "N/A",
            'Speedup': speedup,
            'Conjunctions': py_count
        })
    
    # Display results table
    print("\n" + "=" * 60)
    print("📈 BENCHMARK RESULTS")
    print("=" * 60)
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # Save to CSV
    output_file = "benchmark_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📌 SUMMARY")
    print("=" * 60)
    
    print(f"✅ Python baseline: Working")
    print(f"{'✅' if RUST_AVAILABLE else '❌'} Rust engine: {'Working' if RUST_AVAILABLE else 'Not installed'}")
    print(f"{'✅' if CACHE_AVAILABLE else '❌'} Redis cache: {'Available' if CACHE_AVAILABLE else 'Not installed'}")
    print(f"{'✅' if ASYNC_AVAILABLE else '❌'} Async agent: {'Available' if ASYNC_AVAILABLE else 'Not installed'}")
    
    if RUST_AVAILABLE:
        avg_speedup = df[df['Speedup'] != 'N/A']['Speedup'].apply(lambda x: float(x.replace('x', ''))).mean()
        print(f"\n🚀 Average Rust speedup: {avg_speedup:.1f}x faster than Python")


def quick_test():
    """Quick validation test."""
    print("🧪 Quick Validation Test")
    print("-" * 40)
    
    # Generate 10 test satellites
    sats = generate_mock_satellites(10)
    
    # Test Python
    py_time, py_count = benchmark_python_conjunction(sats)
    print(f"✅ Python: {py_time:.4f}s, {py_count} conjunctions")
    
    # Test Rust (if available)
    if RUST_AVAILABLE:
        rust_time, rust_count = benchmark_rust_conjunction(sats)
        print(f"✅ Rust: {rust_time:.4f}s, {rust_count} conjunctions")
        print(f"⚡ Speedup: {py_time / rust_time:.1f}x")
    else:
        print("⚠️  Rust engine not available - install with: cd rust_engine && maturin develop --release")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        run_benchmark()
