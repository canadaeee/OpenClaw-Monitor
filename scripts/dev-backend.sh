#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Missing backend virtual environment. Run: bash ./scripts/install-ubuntu.sh or bash ./scripts/install-macos.sh"
  exit 1
fi

cd "$BACKEND_DIR"
"$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
