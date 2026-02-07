#!/bin/bash
set -e

echo "🔨 Building GIA CLI Standalone Binary"
echo "======================================"

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist

# Build the binary
echo ""
echo "Building standalone binary..."
pyinstaller gia.spec

# Verify the binary
echo ""
echo "Verifying binary..."
./dist/gia --version

echo ""
echo "✅ Build complete!"
echo ""
echo "Binary location: ./dist/gia"
echo "Size: $(du -h dist/gia | cut -f1)"
echo ""
echo "To install locally:"
echo "  cp dist/gia /usr/local/bin/"
echo ""
echo "To test:"
echo "  ./dist/gia --help"
