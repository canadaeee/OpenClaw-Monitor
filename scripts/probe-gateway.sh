#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$BACKEND_DIR"
python -c "import sys; sys.path.insert(0, r'$BACKEND_DIR'); from app.collector import OpenClawCollector; from app.settings import load_gateway_settings; print(OpenClawCollector(load_gateway_settings()).probe_http())"
