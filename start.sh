#!/bin/bash

# Configuration
BASE_DIR="/home/ubuntu/sbom-system"
BACKEND_PORT=8888
FRONTEND_PORT=8501
VENV="$BASE_DIR/backend/venv/bin"

echo "================================================="
echo "🛡️  SBOM Supply Chain Security System Launcher"
echo "================================================="

# Clean up existing processes
echo "[1/4] Cleaning up existing processes..."
pkill -9 -f "uvicorn main:app" || true
pkill -9 -f "streamlit run dashboard.py" || true
sleep 1

# Start Backend
echo "[2/4] Starting Backend on port $BACKEND_PORT..."
cd "$BASE_DIR/backend"
nohup "$VENV/uvicorn" main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BASE_DIR/storage/backend.log" 2>&1 &
BACKEND_PID=$!

# Start Frontend
echo "[3/4] Starting Frontend on port $FRONTEND_PORT..."
cd "$BASE_DIR/frontend"
nohup "$VENV/streamlit" run dashboard.py --server.port $FRONTEND_PORT --server.address 0.0.0.0 > "$BASE_DIR/storage/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Verification
sleep 3
echo "[4/4] Verifying services..."

if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend is UP (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check $BASE_DIR/storage/backend.log"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend is UP (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend failed to start. Check $BASE_DIR/storage/frontend.log"
fi

echo "================================================="
echo "Access URLs:"
echo "- Backend API: http://localhost:$BACKEND_PORT/health"
echo "- Dashboard:   http://localhost:$FRONTEND_PORT"
echo "================================================="
echo "Tip: Use SSH port forwarding: ssh -L 8501:localhost:8501 -L 8888:localhost:8888 user@remote"
