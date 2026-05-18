#!/usr/bin/env bash
# start_backend.sh — Run from the repo root
# Usage: bash backend/start_backend.sh [port]

PORT=${1:-8000}
echo "Starting BizPulse API on port $PORT..."
uvicorn backend.main:app --reload --port "$PORT" --host 0.0.0.0
