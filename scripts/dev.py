#!/usr/bin/env python3
"""Run the whole Passly demo locally with one command.

    python scripts/dev.py              # laptop only  → http://localhost:3000
    python scripts/dev.py --tunnel     # + a public HTTPS URL for phones

Starts the FastAPI service and the Next.js dev server together, streams both
logs with a prefix, and shuts everything down cleanly on Ctrl-C.

Why --tunnel exists: the demo ends with a customer adding a real pass to Apple
Wallet on their phone. The phone cannot reach localhost, so the join page and
the .pkpass download both need a public URL. Because the web app proxies the
API under /api (see web/next.config.ts), ONE tunnel to port 3000 covers both,
and the emailed pass link is built from the same origin.

Ctrl-C stops everything.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
WEB_DIR = ROOT / "web"
VENV_PY = API_DIR / ".venv" / "bin" / "python"

API_PORT = 8000
WEB_PORT = 3000

RESET, DIM = "\033[0m", "\033[2m"
COLOURS = {"api": "\033[36m", "web": "\033[35m", "tunnel": "\033[33m", "passly": "\033[32m"}

# (process, human name) so a crash can say which one died.
processes: list[tuple[subprocess.Popen, str]] = []


def say(tag: str, message: str) -> None:
    print(f"{COLOURS.get(tag, '')}[{tag}]{RESET} {message}", flush=True)


def die(message: str) -> None:
    say("passly", f"\033[31m{message}{RESET}")
    shutdown()
    sys.exit(1)


# ── preflight ────────────────────────────────────────────────────────────


def _port_busy(port: int) -> bool:
    import socket

    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def preflight() -> None:
    """Fail fast and loudly, before two servers are half-started."""
    if not VENV_PY.exists():
        die(f"No virtualenv at {VENV_PY}. See the README's API setup.")
    if not (WEB_DIR / "node_modules").exists():
        die("web/node_modules missing. Run: cd web && npm install")
    if not (API_DIR / ".env").exists():
        die("api/.env missing. Copy api/.env.example and set DATABASE_URL.")

    # A leftover server from a previous run is the most common way this fails,
    # and without this check the failure surfaces only after a tunnel is up.
    for port, what in ((API_PORT, "API"), (WEB_PORT, "web")):
        if _port_busy(port):
            die(
                f"Port {port} ({what}) is already in use — probably a server "
                f"still running from a previous session.\n"
                f"        Find it:  lsof -nP -iTCP:{port} -sTCP:LISTEN\n"
                f"        Stop it:  kill $(lsof -t -iTCP:{port} -sTCP:LISTEN)"
            )

    say("passly", "Checking the database…")
    result = subprocess.run(
        [
            str(VENV_PY),
            "-c",
            "from dotenv import load_dotenv; load_dotenv('.env');"
            "import runpy, sys; sys.argv=['check'];"
            "runpy.run_path('../scripts/check_supabase.py', run_name='__main__')",
        ],
        cwd=API_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, result.stderr)
        die(
            "Database check failed. If the Supabase project is paused (free tier "
            "pauses after ~7 days idle), open the dashboard to resume it."
        )
    say("passly", "Database ready.")


# ── tunnel ───────────────────────────────────────────────────────────────


def start_tunnel() -> str:
    """Open a public HTTPS tunnel to the web port and return its URL."""
    if shutil.which("cloudflared"):
        return _cloudflared()
    if shutil.which("ngrok"):
        return _ngrok()
    die(
        "No tunnel tool found. Install either:\n"
        "        brew install cloudflared   (no account needed)\n"
        "        brew install ngrok         (needs a free account)"
    )
    raise AssertionError("unreachable")


def _cloudflared() -> str:
    say("tunnel", "Starting cloudflared…")
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{WEB_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((proc, "cloudflared"))

    url: str | None = None
    deadline = time.time() + 60
    while time.time() < deadline and proc.poll() is None:
        line = proc.stdout.readline()  # type: ignore[union-attr]
        if not line:
            continue
        if "trycloudflare.com" in line and "https://" in line:
            for word in line.split():
                if word.startswith("https://") and "trycloudflare.com" in word:
                    url = word.strip().rstrip(".,")
                    break
        if url:
            break
    if not url:
        die("cloudflared did not report a URL within 60s.")

    threading.Thread(target=_pump, args=(proc, "tunnel"), daemon=True).start()
    return url  # type: ignore[return-value]


def _ngrok() -> str:
    say("tunnel", "Starting ngrok…")
    proc = subprocess.Popen(
        ["ngrok", "http", str(WEB_PORT), "--log", "stdout"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((proc, "ngrok"))
    threading.Thread(target=_pump, args=(proc, "tunnel"), daemon=True).start()

    # ngrok publishes the assigned URL on its local API rather than stdout.
    deadline = time.time() + 45
    while time.time() < deadline:
        if proc.poll() is not None:
            die("ngrok exited. Check `ngrok config check`.")
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as r:
                for t in json.load(r).get("tunnels", []):
                    if t.get("proto") == "https":
                        return t["public_url"]
        except Exception:
            time.sleep(1)
    die("ngrok did not report a public URL within 45s.")
    raise AssertionError("unreachable")


# ── servers ──────────────────────────────────────────────────────────────


def _pump(proc: subprocess.Popen, tag: str) -> None:
    """Stream a child's output with a prefix so three logs stay readable."""
    for line in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
        if line.strip():
            print(f"{COLOURS.get(tag, '')}[{tag}]{RESET} {line.rstrip()}", flush=True)


def start_api(public_url: str | None) -> None:
    env = dict(os.environ)
    if public_url:
        # Emailed pass links must resolve from a phone, so they point at the
        # tunnel's /api prefix rather than localhost.
        env["PASSLY_PUBLIC_URL"] = f"{public_url}/api"
    proc = subprocess.Popen(
        [str(VENV_PY), "-m", "uvicorn", "app.main:app", "--port", str(API_PORT), "--reload"],
        cwd=API_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((proc, "api"))
    threading.Thread(target=_pump, args=(proc, "api"), daemon=True).start()


def start_web() -> None:
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=WEB_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((proc, "web"))
    threading.Thread(target=_pump, args=(proc, "web"), daemon=True).start()


def wait_for(url: str, label: str, timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    say("passly", f"\033[31m{label} did not come up within {timeout}s.{RESET}")
    return False


def shutdown(*_: object) -> None:
    for proc, _ in processes:
        if proc.poll() is None:
            proc.terminate()
    deadline = time.time() + 8
    for proc, _ in processes:
        if proc.poll() is None and time.time() < deadline:
            try:
                proc.wait(timeout=max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tunnel",
        action="store_true",
        help="expose a public HTTPS URL so phones can join and download passes",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, lambda *_: (shutdown(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (shutdown(), sys.exit(0)))

    preflight()

    public_url = start_tunnel() if args.tunnel else None
    if public_url:
        say("tunnel", f"Public URL: {public_url}")

    start_api(public_url)
    start_web()

    if not wait_for(f"http://localhost:{API_PORT}/health", "API"):
        die("API failed to start — see the [api] lines above.")
    if not wait_for(f"http://localhost:{WEB_PORT}/", "Web"):
        die("Web failed to start — see the [web] lines above.")

    base = public_url or f"http://localhost:{WEB_PORT}"
    print()
    say("passly", "\033[1mReady.\033[0m")
    say("passly", f"  Founder      {base}/design")
    say("passly", f"  API docs     http://localhost:{API_PORT}/docs")
    if public_url:
        say("passly", f"  Customers    {base}/join/<shopId>   {DIM}(open on a phone){RESET}")
    else:
        say("passly", f"  {DIM}No tunnel: phones cannot reach this. Re-run with --tunnel.{RESET}")
    print()

    try:
        while True:
            for proc, name in processes:
                if proc.poll() is not None:
                    die(f"{name!r} exited (code {proc.returncode}) — "
                        f"shutting the rest down. See the [{name}] lines above.")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
