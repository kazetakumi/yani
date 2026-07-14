"""Cross-platform equivalent of tunnel.sh.

Starts the yani server and exposes it publicly via a Cloudflare Tunnel
"quick tunnel" (free, no account or domain needed). Quick tunnels don't
support a fixed subdomain — cloudflared assigns a random
https://<random-words>.trycloudflare.com URL each run.
Press Ctrl+C to stop both processes.
"""

import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

PORT = 8000
TRYCLOUDFLARE_URL_RE = re.compile(r"https://[a-zA-Z0-9-]*\.trycloudflare\.com")

ROOT = Path(__file__).parent


def _server_ready(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
        return True
    except Exception:
        return False


def main() -> None:
    # Windows' console defaults to cp1252, which can't encode the ✓/⚠ below —
    # reconfigure stdout to UTF-8 so this doesn't crash after the tunnel is
    # already up and the server is running.
    sys.stdout.reconfigure(encoding="utf-8")

    server_proc: subprocess.Popen | None = None
    tunnel_proc: subprocess.Popen | None = None
    log_path: Path | None = None

    def _cleanup(*_):
        print("\nStopping tunnel and server...")
        for proc in (tunnel_proc, server_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        if log_path is not None:
            try:
                log_path.unlink(missing_ok=True)
            except OSError:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    uv = shutil.which("uv")
    if not uv:
        sys.exit("ERROR: 'uv' not found on PATH — install it first.")
    npx = shutil.which("npx")
    if not npx:
        sys.exit("ERROR: 'npx' not found on PATH — install Node.js first.")

    print(f"Starting yani server on port {PORT}...")
    server_proc = subprocess.Popen(
        [uv, "run", "server"],
        cwd=ROOT,
    )

    for _ in range(30):
        if _server_ready(PORT):
            break
        if server_proc.poll() is not None:
            sys.exit(f"ERROR: server exited early (code {server_proc.returncode})")
        time.sleep(0.5)
    else:
        server_proc.terminate()
        sys.exit("ERROR: server did not become ready within 15 s")

    print("Starting cloudflared quick tunnel...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as log_f:
        log_path = Path(log_f.name)

    with open(log_path, "w") as log_out:
        tunnel_proc = subprocess.Popen(
            [npx, "--yes", "cloudflared", "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
            stdout=log_out,
            stderr=subprocess.STDOUT,
        )

    got_url = ""
    for _ in range(30):
        time.sleep(0.5)
        text = log_path.read_text(errors="replace")
        match = TRYCLOUDFLARE_URL_RE.search(text)
        if match:
            got_url = match.group(0)
            break

    if got_url:
        print(f"✓ Live at {got_url}")
        print("  (random each run — re-run this script if you need a new one)")
    else:
        print("⚠ Couldn't read cloudflared's assigned URL — check the output above.")

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
