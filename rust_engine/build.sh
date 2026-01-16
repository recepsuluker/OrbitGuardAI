#!/bin/bash
# Build script for Rust orbital mechanics engine

echo "🦀 Building Rust engine..."

# Install maturin if not already installed
if ! command -v maturin &> /dev/null; then
    echo "📦 Installing maturin..."
    pip install maturin
fi

# Build in release mode (optimized)
echo "🔨 Compiling Rust code (release mode)..."
maturin develop --release

# Test if module loads
echo "✅ Testing module import..."
python -c "import orbit_core; print('Rust engine loaded successfully!')"

echo "🎉 Build complete!"
