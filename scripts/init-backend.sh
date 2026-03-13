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
"$VENV_PYTHON" -c "import sys; sys.path.insert(0, r'$BACKEND_DIR'); from app.db import init_db; init_db(); print('SQLite initialized')"
