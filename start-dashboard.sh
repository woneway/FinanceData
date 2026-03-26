#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

VENV=".venv/bin"
PORT="${DASHBOARD_PORT:-8100}"
FRONTEND_DIR="$ROOT_DIR/frontend"
STATIC_DIR="$ROOT_DIR/src/finance_data/dashboard/static"

usage() {
    cat <<EOF
Usage: $(basename "$0") [command]

Commands:
  dev       Start API + frontend dev server (hot reload)
  prod      Build frontend & start API serving static files
  build     Build frontend only
  api       Start API server only

Options:
  DASHBOARD_PORT=8100   Override API port (default: 8100)

Examples:
  ./start-dashboard.sh dev
  ./start-dashboard.sh prod
  DASHBOARD_PORT=9000 ./start-dashboard.sh prod
EOF
    exit 1
}

check_deps() {
    if [[ ! -x "$VENV/python" ]]; then
        echo "Error: .venv not found. Run: python3 -m venv .venv && $VENV/pip install -e '.[dashboard]'"
        exit 1
    fi
    # Ensure dashboard deps installed
    if ! "$VENV/python" -c "import fastapi" 2>/dev/null; then
        echo "Installing dashboard dependencies..."
        "$VENV/pip" install -e ".[dashboard]"
    fi
}

check_frontend_deps() {
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        echo "Installing frontend dependencies..."
        (cd "$FRONTEND_DIR" && pnpm install)
    fi
}

build_frontend() {
    check_frontend_deps
    echo "Building frontend..."
    (cd "$FRONTEND_DIR" && pnpm build)
    echo "Frontend built → $STATIC_DIR"
}

cmd_dev() {
    check_deps
    check_frontend_deps
    echo "Starting dev mode: API :$PORT + frontend :5173"
    echo "  Dashboard UI → http://localhost:5173"
    echo "  API docs     → http://localhost:$PORT/docs"
    echo ""

    # Start API in background
    "$VENV/python" -c "
import uvicorn
from finance_data.dashboard.app import app
uvicorn.run(app, host='0.0.0.0', port=$PORT, reload=True, reload_dirs=['src'])
" &
    API_PID=$!

    # Start frontend dev server
    (cd "$FRONTEND_DIR" && pnpm dev) &
    FE_PID=$!

    trap 'kill $API_PID $FE_PID 2>/dev/null; wait' EXIT INT TERM
    wait
}

cmd_prod() {
    check_deps
    if [[ ! -f "$STATIC_DIR/index.html" ]]; then
        build_frontend
    fi
    echo "Starting production mode on :$PORT"
    echo "  Dashboard → http://localhost:$PORT"
    echo "  API docs  → http://localhost:$PORT/docs"
    "$VENV/python" -c "
import uvicorn
from finance_data.dashboard.app import app
uvicorn.run(app, host='0.0.0.0', port=$PORT)
"
}

cmd_build() {
    build_frontend
}

cmd_api() {
    check_deps
    echo "Starting API only on :$PORT"
    "$VENV/python" -c "
import uvicorn
from finance_data.dashboard.app import app
uvicorn.run(app, host='0.0.0.0', port=$PORT)
"
}

case "${1:-}" in
    dev)  cmd_dev  ;;
    prod) cmd_prod ;;
    build) cmd_build ;;
    api)  cmd_api  ;;
    *)    usage    ;;
esac
