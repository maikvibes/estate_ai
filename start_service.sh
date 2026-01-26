#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the Estate AI services.
# Usage: ./start_service.sh [api|worker|both]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/Scripts/python}"
DEFAULT_MODE="worker"

usage() {
  cat <<'EOF'
Usage: start_service.sh [api|worker|both]

Modes:
  api     Start FastAPI server (uvicorn app.main:app)
  worker  Start background worker (app.worker)
  both    Run worker in background, then API in foreground

Environment variables:
  PYTHON_BIN   Path to python interpreter (default: .venv/Scripts/python)
EOF
}

ensure_python() {
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python interpreter not found at $PYTHON_BIN" >&2
    exit 1
  fi
}

start_api() {
  echo "Starting API server..."
  exec "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

start_worker() {
  echo "Starting worker..."
  exec "$PYTHON_BIN" -m app.worker
}

start_both() {
  echo "Starting worker in background..."
  "$PYTHON_BIN" -m app.worker &
  WORKER_PID=$!
  trap "echo 'Stopping worker'; kill $WORKER_PID" INT TERM
  echo "Starting API server in foreground..."
  "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

main() {
  local mode="${1:-$DEFAULT_MODE}"
  case "$mode" in
    -h|--help)
      usage
      exit 0
      ;;
    api|worker|both)
      ;;
    *)
      echo "Unknown mode: $mode" >&2
      usage
      exit 1
      ;;
  esac

  ensure_python

  case "$mode" in
    api) start_api ;;
    worker) start_worker ;;
    both) start_both ;;
  esac
}

main "$@"
