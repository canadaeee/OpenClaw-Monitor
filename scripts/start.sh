#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  Linux)
    exec bash "$SCRIPT_DIR/start-ubuntu.sh"
    ;;
  Darwin)
    exec bash "$SCRIPT_DIR/start-macos.sh"
    ;;
  *)
    echo "Unsupported platform for start.sh. Use start-windows.ps1 on Windows."
    exit 1
    ;;
esac
