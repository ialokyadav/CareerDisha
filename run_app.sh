#!/bin/bash

# Resume Parser AI - Unified Start Script

# Function to handle shutdown
cleanup() {
    echo -e "\n\033[1;31mShutting down services...\033[0m"
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    exit
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

# 1. Free backend port if an old process is still running
EXISTING_PIDS=$(lsof -ti tcp:8000 -sTCP:LISTEN 2>/dev/null || true)
if [ -n "$EXISTING_PIDS" ]; then
    echo -e "\033[1;33m[Backend]\033[0m Port 8000 is busy. Stopping old process(es): $EXISTING_PIDS"
    echo "$EXISTING_PIDS" | xargs kill -TERM 2>/dev/null || true
    sleep 1
    REMAINING_PIDS=$(lsof -ti tcp:8000 -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo -e "\033[1;33m[Backend]\033[0m Force-stopping process(es): $REMAINING_PIDS"
        echo "$REMAINING_PIDS" | xargs kill -KILL 2>/dev/null || true
    fi
fi

# 2. Start Backend (production-like via gunicorn)
echo -e "\033[1;32m[Backend]\033[0m Starting Gunicorn on http://127.0.0.1:8000"
cd "backend" || { echo "Backend directory not found"; exit 1; }
source "../.venv/bin/activate" || { echo "Virtual environment not found at ../.venv"; exit 1; }
export DJANGO_DEBUG=1
LOG_DIR="../logs"
mkdir -p "$LOG_DIR"
echo -e "\033[1;32m[Backend]\033[0m Logs: $LOG_DIR/backend.log"
# Use process substitution so BACKEND_PID points to gunicorn (not tee).
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 1 --reload --access-logfile - --error-logfile - > >(tee "$LOG_DIR/backend.log") 2>&1 &
BACKEND_PID=$!
cd ..

# 3. Wait a moment for backend to initialize
sleep 2

# 4. Start Frontend
echo -e "\033[1;36m[Frontend]\033[0m Starting Vite dev server..."
cd "frontend" || { echo "Frontend directory not found"; exit 1; }
npm run dev

# If npm run dev exits for some reason, cleanup backend too
cleanup
