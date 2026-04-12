#!/usr/bin/env bash
# Video Downloader - One-Click Setup & Launch
# Works on Mac, Linux, and Windows (Git Bash/WSL)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  =================================="
echo "    Video Downloader - Setup"
echo "  =================================="
echo ""

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "  [ERROR] Python not found."
    echo "  Install Python from: https://python.org/downloads"
    exit 1
fi

echo "  Using: $($PYTHON --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# Install dependencies
echo "  Installing dependencies..."
pip install -q -r requirements.txt

# Create downloads folder
mkdir -p downloads

echo ""
echo "  =================================="
echo "    Setup Complete!"
echo "  =================================="
echo ""
echo "  Starting Video Downloader..."
echo "  Open your browser to: http://localhost:5000"
echo ""

python app.py
