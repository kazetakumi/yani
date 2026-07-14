#!/usr/bin/env bash
# Starts the yani server and exposes it publicly via a Cloudflare Tunnel
# "quick tunnel" (free, no account or domain needed). Quick tunnels don't
# support a fixed subdomain — cloudflared assigns a random
# https://<random-words>.trycloudflare.com URL each run, printed once the
# tunnel is up. Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PORT=8000
TUNNEL_LOG="$(mktemp)"

cleanup() {
    echo ""
    echo "Stopping tunnel and server..."
    [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
    [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null || true
    rm -f "$TUNNEL_LOG"
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

echo "Starting cloudflared quick tunnel..."
# Tee, not a plain background pipe: cloudflared's URL line still needs to
# reach your terminal live, but a copy also needs to land in a file this
# script can grep — a subshell pipeline can't export $! for the real
# tunnel process, so PIPESTATUS/direct redirection is used instead.
npx --yes cloudflared tunnel --url "http://127.0.0.1:$PORT" > >(tee "$TUNNEL_LOG") 2>&1 &
TUNNEL_PID=$!

# Up to ~15s for cloudflared to print "https://<random-words>.trycloudflare.com".
GOT_URL=""
for _ in $(seq 1 30); do
    if grep -qo 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null; then
        GOT_URL="$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" | head -1)"
        break
    fi
    sleep 0.5
done

if [[ -n "$GOT_URL" ]]; then
    echo "✓ Live at $GOT_URL"
    echo "  (random each run — re-run this script if you need a new one)"
else
    echo "⚠ Couldn't read cloudflared's assigned URL — check the output above."
fi

wait "$SERVER_PID" "$TUNNEL_PID"
