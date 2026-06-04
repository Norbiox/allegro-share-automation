#!/usr/bin/env bash
set -euo pipefail

HOST="allegro@192.168.0.11"
APP_DIR="/opt/allegro-share-automation"

echo "==> Pulling latest code..."
ssh "$HOST" "git -C $APP_DIR pull"

echo "==> Syncing dependencies..."
ssh "$HOST" "cd $APP_DIR && uv sync --frozen"

echo "==> Restarting service..."
ssh "$HOST" "sudo systemctl restart allegro-share"

echo "==> Health check..."
for i in $(seq 1 10); do
  if ssh "$HOST" "curl -sf http://localhost:5000/health" > /dev/null 2>&1; then
    echo "==> Service is up."
    exit 0
  fi
  sleep 2
done

echo "ERROR: Health check timed out." >&2
exit 1
