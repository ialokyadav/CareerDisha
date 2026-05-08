#!/bin/bash

# Resume Parser AI - Unified Start Script

BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

# Function to handle shutdown
cleanup() {
    echo -e "\n\033[1;31mShutting down services...\033[0m"
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    exit
}

free_port() {
    local port="$1"
    local label="$2"
    local existing_pids
    local remaining_pids

    existing_pids=$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$existing_pids" ]; then
        echo -e "\033[1;33m[$label]\033[0m Port ${port} is busy. Stopping old process(es): $existing_pids"
        echo "$existing_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 1
        remaining_pids=$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "\033[1;33m[$label]\033[0m Force-stopping process(es): $remaining_pids"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
    fi
}

# Trap Ctrl+C and kill signal
trap cleanup SIGINT SIGTERM

echo -e "\033[1;34m========================================\033[0m"
echo -e "\033[1;34m    Starting Resume Parser AI...       \033[0m"
echo -e "\033[1;34m========================================\033[0m"

# 0. Check MongoDB (Optional warning)
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "\033[1;33m[Warning]\033[0m MongoDB (mongod) does not seem to be running."
    echo -e "          Ensure your MongoDB instance is active if connection errors occur."
fi

# 1. Free project ports if old processes are still running
free_port "$BACKEND_PORT" "Backend"
free_port "$FRONTEND_PORT" "Frontend"

# 2. Start Backend (production-like via gunicorn)
echo -e "\033[1;32m[Backend]\033[0m Starting Gunicorn on ${BACKEND_URL}"
cd "backend" || { echo "Backend directory not found"; exit 1; }
source "../.venv/bin/activate" || { echo "Virtual environment not found at ../.venv"; exit 1; }
export DJANGO_DEBUG=1
LOG_DIR="../logs"
mkdir -p "$LOG_DIR"
echo -e "\033[1;32m[Backend]\033[0m Logs: $LOG_DIR/backend.log"
# Use process substitution so BACKEND_PID points to gunicorn (not tee).
gunicorn config.wsgi:application --bind "127.0.0.1:${BACKEND_PORT}" --workers 1 --reload --access-logfile - --error-logfile - > >(tee "$LOG_DIR/backend.log") 2>&1 &
BACKEND_PID=$!
cd ..

# 3. Wait a moment for backend to initialize
sleep 2

# 4. Start Frontend
echo -e "\033[1;36m[Frontend]\033[0m Starting Vite dev server..."
echo -e "\033[1;36m[Frontend]\033[0m Open ${FRONTEND_URL}/login in your browser"
echo -e "\033[1;36m[Frontend]\033[0m API remains available at ${BACKEND_URL}"
cd "frontend" || { echo "Frontend directory not found"; exit 1; }
npm run dev -- --host 127.0.0.1 --strictPort

# If npm run dev exits for some reason, cleanup backend too
cleanup
