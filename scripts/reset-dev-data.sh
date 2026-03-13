#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  Darwin)
    exec bash "$SCRIPT_DIR/reset-dev-data-macos.sh"
    ;;
  Linux)
    exec bash "$SCRIPT_DIR/reset-dev-data-ubuntu.sh"
    ;;
  *)
    echo "Unsupported platform for reset-dev-data.sh"
    exit 1
    ;;
esac
