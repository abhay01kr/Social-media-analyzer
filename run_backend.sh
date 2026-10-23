#!/usr/bin/env bash

# Resolve project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "=================================================="
echo " Starting Social Media Analyzer Backend Server"
echo "=================================================="

# 1. Clean up any stale process holding port 8000
EXISTING_PID=$(lsof -ti :8000)
if [ -n "$EXISTING_PID" ]; then
    echo "• Freeing port 8000 (terminating existing PID: $EXISTING_PID)..."
    kill -9 $EXISTING_PID 2>/dev/null || true
    sleep 1
fi

# 2. Navigate to backend and activate Python virtual environment
cd "$BACKEND_DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found in $BACKEND_DIR/.venv"
    exit 1
fi

echo "• Python Environment: $(which python)"
echo "• Backend Port: 8000"
echo "• API Docs: http://127.0.0.1:8000/docs"
echo "• Dashboard API: http://127.0.0.1:8000/dashboard"
echo "=================================================="
echo "Server starting with auto-reload (Press Ctrl+C to stop)..."
echo ""

# 3. Launch Uvicorn
uvicorn main:app --reload --port 8000
