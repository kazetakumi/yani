#!/usr/bin/env bash
# Starts the yani server and exposes it publicly at https://yani.loca.lt
# via localtunnel (free, no account needed). Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

SUBDOMAIN="yani"
PORT=8000

cleanup() {
    echo ""
    echo "Stopping tunnel and server..."
    [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
    [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting yani server on port $PORT..."
uv run server &
SERVER_PID=$!

# Wait for the server to accept connections before starting the tunnel.
for _ in $(seq 1 30); do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
        break
    fi
    sleep 0.5
done

echo "Starting localtunnel with subdomain '$SUBDOMAIN'..."
echo "First-time visitors will see a localtunnel interstitial page — that's expected."
npx --yes localtunnel --port "$PORT" --subdomain "$SUBDOMAIN" &
TUNNEL_PID=$!

wait "$SERVER_PID" "$TUNNEL_PID"
