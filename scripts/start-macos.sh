#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing backend virtual environment. Run: bash ./scripts/install-macos.sh"
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

wait
