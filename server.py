#!/usr/bin/env python3
"""
Maha Transcribe local server.

Serves maha_transcribe.html over http://localhost so the browser treats it as
a secure context and allows microphone access (getUserMedia refuses to work
on a plain file:// page on most Android browsers).

If the preferred port is already taken (another instance still running, or
something else on the phone using it) this automatically tries the next
ports up instead of crashing, and prints whichever port it actually bound to.
"""
import http.server
import socket
import socketserver
import sys
import webbrowser
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFERRED_PORT = 8420
MAX_ATTEMPTS = 50
APP_FILE = "maha_transcribe.html"


def find_open_port(preferred: int, attempts: int = MAX_ATTEMPTS) -> int:
    """Try the preferred port first, then keep counting up until one binds."""
    for port in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue  # taken, try the next one
            return port
    raise RuntimeError(
        f"no free port found between {preferred} and {preferred + attempts - 1}"
    )


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet, errors still surface via exceptions

    def end_headers(self):
        # local dev server only, never exposed beyond localhost
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def try_open_browser(url: str) -> bool:
    # Termux has no default `xdg-open`/webbrowser backend, but the Termux:API
    # add-on exposes `termux-open-url`, which hands the link to the real
    # Android browser. Fall back to Python's webbrowser everywhere else.
    if shutil.which("termux-open-url"):
        try:
            subprocess.run(["termux-open-url", url], check=False)
            return True
        except Exception:
            return False
    try:
        return webbrowser.open(url)
    except Exception:
        return False


def main():
    if not (ROOT / APP_FILE).exists():
        print(f"error: {APP_FILE} not found next to server.py in {ROOT}")
        sys.exit(1)

    requested = PREFERRED_PORT
    if len(sys.argv) > 1:
        try:
            requested = int(sys.argv[1])
        except ValueError:
            print(f"ignoring invalid port argument {sys.argv[1]!r}, using {PREFERRED_PORT}")

    port = find_open_port(requested)
    if port != requested:
        print(f"port {requested} is already in use, using {port} instead")

    url = f"http://127.0.0.1:{port}/{APP_FILE}"
    with ReusableServer(("127.0.0.1", port), Handler) as httpd:
        print(f"maha transcribe running at {url}")
        print("press ctrl+c to stop")
        opened = try_open_browser(url)
        if not opened:
            print("could not auto-open a browser, open the address above manually")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
