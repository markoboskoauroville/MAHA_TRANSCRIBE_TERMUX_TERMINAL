"""
Maha Transcribe
Mantra Productions

A Flask front end for one job: hand the browser maha_transcribe.html over
http://127.0.0.1 rather than file://, which is what lets getUserMedia (the
microphone) work at all on Android's browsers -- they refuse it on a plain
file:// page.

Run:  python3 app.py        then open http://127.0.0.1:8420

Built to the same house pattern as GDRIVE_DOWNLOADER_FLASK_MACOS: portpick
so a busy port never stops the app from starting, localguard so a page open
in another tab cannot poke at this one, and the same terminal console. This
app carries no server-side state of its own -- every key, transcript and
setting lives in the browser's localStorage -- so it is a much smaller
version of that pattern, not a rewrite of it.
"""

import os
import sys
import time

from flask import Flask, Response, jsonify, request, send_from_directory

import audioprep
import console as term
import localguard
import portpick
import selfupdate
import version

APP_VERSION = version.APP_VERSION      # one whole number, per modules/versioning.md
DEFAULT_PORT = 8420

HERE = os.path.dirname(os.path.abspath(__file__))
APP_FILE = "maha_transcribe.html"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = audioprep.MAX_UPLOAD_BYTES

START_TIME = time.time()
REQUEST_COUNT = 0
OPTIMIZE_COUNT = 0
BYTES_SAVED = 0

# The port ACTUALLY bound, which is not always the preferred one. Set once at
# startup and read from here everywhere downstream, so no part of the app can
# be left believing the wrong number -- localguard checks the Host header
# against this, and telling it the wrong port would refuse every request
# from the very page that was just opened.
LIVE_PORT = DEFAULT_PORT


@app.before_request
def gate():
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    return localguard.check(LIVE_PORT)


@app.route("/")
def index():
    return send_from_directory(HERE, APP_FILE)


@app.route("/" + APP_FILE)
def app_file_direct():
    # the app itself sometimes links to its own filename directly (the old
    # file:// habit); answer that the same way rather than 404ing on it
    return send_from_directory(HERE, APP_FILE)


@app.route("/favicon.ico")
def favicon_ico():
    return ("", 204)


@app.route("/api/ffmpeg")
def api_ffmpeg():
    """So the page can ask, before offering a video file, whether the
    server side of the pipeline is actually there to receive it."""
    return jsonify({"available": audioprep.available()})


@app.route("/api/optimize-audio", methods=["POST"])
def api_optimize_audio():
    """Take any file ffmpeg can decode, hand back small mono speech Opus.

    The result never touches disk longer than the request: audioprep
    writes to a temp directory and removes it before this returns, whether
    the conversion succeeded or not.
    """
    global OPTIMIZE_COUNT, BYTES_SAVED

    f = request.files.get("file")
    if f is None:
        return jsonify({"error": "no file arrived"}), 400
    raw = f.read()
    if not raw:
        return jsonify({"error": "that file is empty"}), 400

    try:
        out_bytes, meta = audioprep.optimize(raw, f.filename or "")
    except audioprep.AudioPrepError as e:
        return jsonify({"error": str(e)}), 422

    OPTIMIZE_COUNT += 1
    BYTES_SAVED += max(0, meta["original_bytes"] - meta["optimized_bytes"])

    resp = Response(out_bytes, mimetype="audio/ogg")
    resp.headers["X-Original-Bytes"] = str(meta["original_bytes"])
    resp.headers["X-Optimized-Bytes"] = str(meta["optimized_bytes"])
    resp.headers["X-Convert-Seconds"] = str(meta["convert_seconds"])
    if meta["duration_seconds"] is not None:
        resp.headers["X-Duration-Seconds"] = str(meta["duration_seconds"])
    return resp


def console_snapshot():
    return {
        "version": APP_VERSION,
        "uptime": time.time() - START_TIME,
        "requests": REQUEST_COUNT,
        "optimized": OPTIMIZE_COUNT,
        "saved_mb": BYTES_SAVED / 1048576.0,
        "ffmpeg": audioprep.available(),
    }


if __name__ == "__main__":
    if not os.path.exists(os.path.join(HERE, APP_FILE)):
        print(f"error: {APP_FILE} not found next to app.py in {HERE}")
        sys.exit(1)

    requested = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            requested = int(sys.argv[1])
        except ValueError:
            print(f"ignoring invalid port argument {sys.argv[1]!r}, using {DEFAULT_PORT}")

    # NEVER refuse to start over a busy port. Very often the thing holding it
    # is another copy of this app, still running from before.
    LIVE_PORT, port_note = portpick.pick("127.0.0.1", requested)

    action = term.run(app, "127.0.0.1", LIVE_PORT, snapshot=console_snapshot,
                      note=port_note, on_check_update=selfupdate.check_remote,
                      on_perform_update=selfupdate.perform_update)
    if action == "restart":
        os.execv(sys.executable, [sys.executable] + sys.argv)
