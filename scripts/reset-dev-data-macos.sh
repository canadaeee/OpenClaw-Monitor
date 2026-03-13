#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

for target in "$DATA_DIR/monitor.db" "$DATA_DIR/raw-events.jsonl" "$DATA_DIR/node-events.jsonl"; do
  if [[ -f "$target" ]]; then
    rm -f "$target"
    echo "Removed $target"
  else
    echo "Skipped missing $target"
  fi
done

echo "Reinitializing SQLite database"
python3 -c "import sys; sys.path.insert(0, r'$PROJECT_ROOT/backend'); from app.db import init_db; init_db(); print('database initialized')"

echo "Development data reset complete."
