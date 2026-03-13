#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "[1/5] Checking runtime requirements"
command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }
python3 -m pip --version >/dev/null 2>&1 || { echo "python3-pip is required"; exit 1; }
[[ -f "$BACKEND_DIR/requirements.txt" ]] || { echo "Missing backend/requirements.txt"; exit 1; }
[[ -f "$FRONTEND_DIR/package.json" ]] || { echo "Missing frontend/package.json"; exit 1; }

echo "[2/5] Installing backend dependencies"
cd "$BACKEND_DIR"
python3 -m pip install -r requirements.txt

echo "[3/5] Initializing SQLite database"
python3 -c "import sys; sys.path.insert(0, r'$BACKEND_DIR'); from app.db import init_db; init_db(); print('database initialized')"

echo "[4/5] Installing frontend dependencies"
cd "$FRONTEND_DIR"
npm install

echo "[5/5] Building frontend"
npm run build

echo
echo "OpenClaw Monitor install complete."
echo "Start with: bash ./scripts/start-macos.sh"
