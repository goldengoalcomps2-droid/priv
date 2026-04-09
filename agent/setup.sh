#!/bin/bash
# Quick setup for Mac Agent

set -e

echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Done! To run the agent:"
echo ""
echo "  export ANTHROPIC_API_KEY=sk-ant-..."
echo "  python3 agent.py"
echo ""
echo "NOTE: On first run, macOS will ask for Screen Recording"
echo "and Accessibility permissions for Terminal. Grant both."
