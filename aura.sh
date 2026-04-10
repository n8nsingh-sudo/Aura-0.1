#!/bin/bash

# AURA 2.0 Robust Starter
# This script handles zombie processes and ensures a clean startup.

echo "🚀 Starting AURA..."

# 1. Kill any existing instances on port 8080 (Dashboard)
PORT=8080
PID=$(lsof -ti :$PORT)
if [ -z "$PID" ]; then
    echo "✓ Port $PORT is free"
else
    echo "⚠ Port $PORT is occupied (PID: $PID). Clearing zombie process..."
    kill -9 $PID
    sleep 1
fi

# 2. Kill any zombie audio playback processes (afplay on Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    pkill afplay 2>/dev/null
    echo "✓ Zombie audio processes cleared"
fi

# 3. Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# 4. Start AURA
python3 main.py
