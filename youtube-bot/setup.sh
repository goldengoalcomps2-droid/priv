#!/bin/bash
# YouTube Bot — One-click setup script for macOS
# Run this from any directory: bash <(curl -s ...) OR save and run: bash setup.sh

set -e

echo "========================================="
echo "  YouTube Bot — Setup"
echo "========================================="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required. Install it with: brew install python3"
    exit 1
fi

# Check for Git
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is required. Install it with: brew install git"
    exit 1
fi

# Clone or update the repo
REPO_DIR="$HOME/youtube-bot-app"
if [ -d "$REPO_DIR" ]; then
    echo "[1/4] Updating existing repo..."
    cd "$REPO_DIR"
    git fetch origin claude/youtube-automation-bot-OvjRp
    git checkout claude/youtube-automation-bot-OvjRp
    git pull origin claude/youtube-automation-bot-OvjRp
else
    echo "[1/4] Cloning repository..."
    git clone https://github.com/goldengoalcomps2-droid/priv.git "$REPO_DIR"
    cd "$REPO_DIR"
    git checkout claude/youtube-automation-bot-OvjRp
fi

cd "$REPO_DIR/youtube-bot"

# Install Python dependencies
echo "[2/4] Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Playwright browsers (skip webkit on older macOS)
echo "[3/4] Installing browser binaries (Chromium + Firefox)..."
python3 -m playwright install chromium firefox

echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "  To run the bot:"
echo "    cd $REPO_DIR/youtube-bot"
echo "    python3 main.py --interactive"
echo ""
echo "  Or run your full session:"
echo "    python3 main.py --file example_instructions.txt"
echo ""
echo "========================================="
echo ""

# Ask if they want to start now
read -p "Start the bot now in interactive mode? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 main.py --interactive
fi
