#!/bin/bash

# ==========================================================
# 🛡️ SBOM Supply Chain Security System - One-Click Launcher
# ==========================================================

BASE_DIR="/home/ubuntu/sbom-system"
BACKEND_PORT=8888
FRONTEND_PORT=8501
VENV_BIN="$BASE_DIR/backend/venv/bin"
LOG_DIR="$BASE_DIR/storage/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "----------------------------------------------------"
echo "Step 1: Cleaning up existing processes..."
pkill -9 -f "uvicorn main:app" || true
pkill -9 -f "streamlit run dashboard.py" || true
sleep 2

echo "Step 2: Starting Backend (FastAPI) on 0.0.0.0:$BACKEND_PORT..."
cd "$BASE_DIR/backend"
nohup "$VENV_BIN/uvicorn" main:app --host 0.0.0.0 --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "Step 3: Starting Frontend (Streamlit) on 0.0.0.0:$FRONTEND_PORT..."
cd "$BASE_DIR/frontend"
nohup "$VENV_BIN/streamlit" run dashboard.py --server.address 0.0.0.0 --server.port $FRONTEND_PORT > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "----------------------------------------------------"
echo "Step 4: Verifying Services..."
sleep 5

if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend is RUNNING (PID: $BACKEND_PID)"
else
    echo "❌ Backend FAILED to start. See $LOG_DIR/backend.log"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend is RUNNING (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend FAILED to start. See $LOG_DIR/frontend.log"
fi

echo "----------------------------------------------------"
echo "Access Information:"
echo "Dashboard (WebUI): http://<Your-IP>:$FRONTEND_PORT"
echo "Backend API:       http://<Your-IP>:$BACKEND_PORT/health"
echo "----------------------------------------------------"
echo "Use 'disown' to ensure processes survive terminal close if needed."
disown -a
echo "Done."
