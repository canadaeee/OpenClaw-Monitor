#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_VENV="$PROJECT_ROOT/backend/.venv"

ensure_installed() {
  if [[ -x "$BACKEND_VENV/bin/python" ]]; then
    return 0
  fi
  echo "Backend venv not found. Running installer..."
  bash "$SCRIPT_DIR/install.sh"
}

ensure_installed
exec bash "$SCRIPT_DIR/start.sh"

