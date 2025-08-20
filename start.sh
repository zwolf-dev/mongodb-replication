#!/usr/bin/env bash
set -euo pipefail

# Start the FastAPI MongoDB Replication Orchestrator
# - Creates/uses local .venv
# - Installs dependencies
# - Runs uvicorn on port 8000

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if [ ! -d .venv ]; then
	echo "Creating virtual environment (.venv)..."
	python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"

echo "Starting server at http://$HOST:$PORT ..."
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
