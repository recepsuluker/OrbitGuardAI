@echo off
REM Build script for Rust orbital mechanics engine (Windows)

echo 🦀 Building Rust engine...

REM Install maturin if not already installed
pip show maturin >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing maturin...
    pip install maturin
)

REM Build in release mode (optimized)
echo 🔨 Compiling Rust code ^(release mode^)...
cd src
cd ..
maturin develop --release

REM Test if module loads
echo ✅ Testing module import...
python -c "import orbit_core; print('Rust engine loaded successfully!')"

echo 🎉 Build complete!
pause
