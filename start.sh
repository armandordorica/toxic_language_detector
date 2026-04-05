#!/bin/bash
set -e

PORT=${PORT:-8000}

echo "Starting app on port $PORT..."
uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
APP_PID=$!

echo "Opening Cloudflare tunnel..."
cloudflared tunnel --url "http://localhost:$PORT" &
TUNNEL_PID=$!

trap "echo 'Shutting down...'; kill $APP_PID $TUNNEL_PID 2>/dev/null" EXIT
wait
