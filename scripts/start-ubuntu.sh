#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing backend virtual environment. Run: bash ./scripts/install-ubuntu.sh"
  exit 1
fi

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti tcp:"$port" >/dev/null 2>&1
    return $?
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser "$port"/tcp >/dev/null 2>&1
    return $?
  fi
  return 1
}

if port_in_use 12888; then
  echo "Port 12888 is already in use. Stop existing service with: bash ./scripts/stop-ubuntu.sh"
  exit 1
fi

if port_in_use 12889; then
  echo "Port 12889 is already in use. Stop existing service with: bash ./scripts/stop-ubuntu.sh"
  exit 1
fi

echo "Starting backend on 127.0.0.1:12888"
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 12888
) &

echo "Starting frontend preview on 127.0.0.1:12889"
(
  cd "$FRONTEND_DIR"
  npm run preview
) &

echo
echo "OpenClaw Monitor is starting..."
echo "Dashboard: http://127.0.0.1:12889"
echo "API:       http://127.0.0.1:12888/api/health"

wait
