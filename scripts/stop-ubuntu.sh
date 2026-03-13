#!/usr/bin/env bash
set -euo pipefail

for port in 12888 12889; do
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"$port" || true)"
  else
    pids="$(fuser "$port"/tcp 2>/dev/null || true)"
  fi

  if [[ -z "${pids}" ]]; then
    echo "No listening process found on port ${port}"
    continue
  fi

  for pid in $pids; do
    echo "Stopping process ${pid} on port ${port}"
    kill "$pid" || true
  done
done

echo "OpenClaw Monitor stop routine completed."
