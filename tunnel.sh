#!/usr/bin/env bash
# Starts the yani server and exposes it publicly via localtunnel (free, no
# account needed). Requests the "yani" subdomain (https://yani.loca.lt), but
# localtunnel hands that out first-come-first-served — if someone else is
# holding it, it silently substitutes a random *.loca.lt URL instead of
# erroring, so this script watches its actual output and says so clearly
# rather than leaving you to notice a wrong URL. Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

SUBDOMAIN="yani"
PORT=8000
WANT_URL="https://${SUBDOMAIN}.loca.lt"
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

echo "Starting localtunnel, requesting subdomain '$SUBDOMAIN'..."
echo "First-time visitors will see a localtunnel interstitial page — that's expected."
# Tee, not a plain background pipe: localtunnel's URL line still needs to
# reach your terminal live, but a copy also needs to land in a file this
# script can grep — a subshell pipeline can't export $! for the real
# tunnel process, so PIPESTATUS/direct redirection is used instead.
npx --yes localtunnel --port "$PORT" --subdomain "$SUBDOMAIN" > >(tee "$TUNNEL_LOG") 2>&1 &
TUNNEL_PID=$!

# Up to ~15s for localtunnel to print "your url is: https://...loca.lt".
GOT_URL=""
for _ in $(seq 1 30); do
    if grep -qo 'https://[a-zA-Z0-9-]*\.loca\.lt' "$TUNNEL_LOG" 2>/dev/null; then
        GOT_URL="$(grep -o 'https://[a-zA-Z0-9-]*\.loca\.lt' "$TUNNEL_LOG" | head -1)"
        break
    fi
    sleep 0.5
done

if [[ "$GOT_URL" == "$WANT_URL" ]]; then
    echo "✓ Live at $WANT_URL"
elif [[ -n "$GOT_URL" ]]; then
    echo "⚠ '$SUBDOMAIN' was already taken by another tunnel — got $GOT_URL instead."
    echo "  Someone else is holding $WANT_URL right now; re-run this script later to retry."
else
    echo "⚠ Couldn't read localtunnel's assigned URL — check the output above."
fi

wait "$SERVER_PID" "$TUNNEL_PID"
