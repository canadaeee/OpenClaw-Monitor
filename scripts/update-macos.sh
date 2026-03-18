#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRANCH="main"

if ! git -C "$PROJECT_ROOT" diff --quiet || ! git -C "$PROJECT_ROOT" diff --cached --quiet; then
  echo "Working tree is not clean. Please commit/stash your changes before update."
  exit 1
fi

echo "[1/3] Updating repository"
git -C "$PROJECT_ROOT" fetch origin "$BRANCH"
git -C "$PROJECT_ROOT" checkout "$BRANCH"
git -C "$PROJECT_ROOT" pull --rebase origin "$BRANCH"

echo "[2/3] Re-running installer"
bash "$SCRIPT_DIR/install-macos.sh"

echo "[3/3] Update complete"
echo "Start with: bash ./scripts/start-macos.sh"
