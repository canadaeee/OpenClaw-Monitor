#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  Darwin)
    exec bash "$SCRIPT_DIR/update-macos.sh"
    ;;
  Linux)
    exec bash "$SCRIPT_DIR/update-ubuntu.sh"
    ;;
  *)
    echo "Unsupported platform for update.sh"
    exit 1
    ;;
esac
