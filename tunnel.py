"""Cross-platform equivalent of tunnel.sh.

Starts the yani server and exposes it publicly via localtunnel.
Requests the "yani" subdomain (https://yani.loca.lt) but reports clearly if
it was already taken and a random subdomain was assigned instead.
Press Ctrl+C to stop both processes.
"""

import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SUBDOMAIN = "yani"
PORT = 8000
WANT_URL = f"https://{SUBDOMAIN}.loca.lt"

ROOT = Path(__file__).parent


def _server_ready(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
        return True
    except Exception:
        return False


def main() -> None:
    server_proc: subprocess.Popen | None = None
    tunnel_proc: subprocess.Popen | None = None

    def _cleanup(*_):
        print("\nStopping tunnel and server...")
        for proc in (tunnel_proc, server_proc):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
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

    print(f"Starting localtunnel, requesting subdomain '{SUBDOMAIN}'...")
    print("First-time visitors will see a localtunnel interstitial page — that's expected.")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as log_f:
        log_path = Path(log_f.name)

    with open(log_path, "w") as log_out:
        tunnel_proc = subprocess.Popen(
            [npx, "--yes", "localtunnel", "--port", str(PORT), "--subdomain", SUBDOMAIN],
            stdout=log_out,
            stderr=subprocess.STDOUT,
        )

    got_url = ""
    for _ in range(30):
        time.sleep(0.5)
        text = log_path.read_text(errors="replace")
        for token in text.split():
            if token.startswith("https://") and ".loca.lt" in token:
                got_url = token.rstrip(".,")
                break
        if got_url:
            break

    log_path.unlink(missing_ok=True)

    if got_url == WANT_URL:
        print(f"✓ Live at {WANT_URL}")
    elif got_url:
        print(f"⚠ '{SUBDOMAIN}' was already taken — got {got_url} instead.")
        print(f"  Someone else is holding {WANT_URL} right now; re-run later to retry.")
    else:
        print("⚠ Couldn't read localtunnel's assigned URL — check the output above.")

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
