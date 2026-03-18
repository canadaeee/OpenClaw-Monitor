#!/usr/bin/env bash
set -euo pipefail

REPO_URL=""
BRANCH="main"
TARGET_DIR="${HOME}/OpenClaw-Monitor"
AUTO_START="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-main}"
      shift 2
      ;;
    --dir)
      TARGET_DIR="${2:-$TARGET_DIR}"
      shift 2
      ;;
    --start)
      AUTO_START="true"
      shift 1
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: curl -fsSL <raw-script-url> | bash -s -- --repo https://github.com/<owner>/<repo>.git"
  exit 1
fi

command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }

if [[ -d "$TARGET_DIR/.git" ]]; then
  echo "Updating existing repository in $TARGET_DIR"
  git -C "$TARGET_DIR" fetch origin "$BRANCH"
  git -C "$TARGET_DIR" checkout "$BRANCH"
  git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH"
else
  echo "Cloning $REPO_URL into $TARGET_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  bash "$TARGET_DIR/scripts/install-macos.sh"
else
  bash "$TARGET_DIR/scripts/install-ubuntu.sh"
fi

if [[ "$AUTO_START" == "true" ]]; then
  exec bash "$TARGET_DIR/scripts/run.sh"
fi
