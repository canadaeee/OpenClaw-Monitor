#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

echo "[1/5] Checking runtime requirements"
command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }
python3 -m venv --help >/dev/null 2>&1 || { echo "python3-venv is required"; exit 1; }
[[ -f "$BACKEND_DIR/requirements.txt" ]] || { echo "Missing backend/requirements.txt"; exit 1; }
[[ -f "$FRONTEND_DIR/package.json" ]] || { echo "Missing frontend/package.json"; exit 1; }

echo "[2/5] Creating backend virtual environment"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

echo "[3/5] Installing backend dependencies"
cd "$BACKEND_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r requirements.txt

echo "[4/5] Initializing SQLite database"
"$VENV_DIR/bin/python" -c "import sys; sys.path.insert(0, r'$BACKEND_DIR'); from app.db import init_db; init_db(); print('database initialized')"

echo "[5/6] Installing frontend dependencies"
cd "$FRONTEND_DIR"
if [[ -f "$FRONTEND_DIR/package-lock.json" ]]; then
  npm ci
else
  npm install
fi

echo "[6/6] Building frontend"
npm run build

echo
echo "OpenClaw Monitor install complete."
echo "Backend virtual environment: $VENV_DIR"
echo "Start with: bash ./scripts/start-ubuntu.sh"
