#!/bin/bash
set -e

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$HF_API_TOKEN" ]; then
  echo "Error: HF_API_TOKEN is not set."
  echo "Copy .env.example to .env and add your token from https://huggingface.co/settings/tokens"
  exit 1
fi

PORT=${PORT:-8000}

# Activate virtual environment if present
if [ -f toxic_language/bin/activate ]; then
  source toxic_language/bin/activate
elif [ -f venv/bin/activate ]; then
  source venv/bin/activate
fi

echo "Starting app on port $PORT..."
uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
APP_PID=$!

echo "Opening Cloudflare tunnel..."
cloudflared tunnel --url "http://localhost:$PORT" &
TUNNEL_PID=$!

trap "echo 'Shutting down...'; kill $APP_PID $TUNNEL_PID 2>/dev/null" EXIT
wait
