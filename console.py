"""
console.py  --  the terminal side of Maha Transcribe.

A server left running should not be a wall of log lines quit with a
two-finger interrupt. This is a live console: one keypress per command, a
dashboard that redraws in place, and the same amber on near-black the page
uses.

Follows the house pattern from GDRIVE_DOWNLOADER_FLASK_MACOS and the block
logo already established in MAHA_TRANSCRIBE_TERMUX_TERMINAL's own README.
Same keys, same shape, because a control that behaves differently depending
on which app you found it in is the thing modules/design-language.md
exists to prevent.

Smaller than the original by design: this app keeps no server-side job
state at all, every key, transcript and setting lives in the browser, so
there is nothing here to pause, verify or sign in to. The dashboard shows
what is actually true of this process: version, address, uptime, and how
many requests it has answered.

DEGRADES HONESTLY. If stdout is not a terminal -- piped to a file, run
under a service manager, run from an editor -- there is no cursor to hide
and no key to press, so it prints plain lines instead and never draws a
frame.
"""

import os
import re
import shutil
import subprocess
import sys
import threading
import time

RESET = "\033[0m"
_ANSI = re.compile(r"\033\[[0-9;]*m")


def vlen(s):
    """Length as the eye sees it: colour codes take no space on screen."""
    return len(_ANSI.sub("", s))


LOGO = [
    "███╗   ███╗ █████╗ ██╗  ██╗ █████╗ ",
    "████╗ ████║██╔══██╗██║  ██║██╔══██╗",
    "██╔████╔██║███████║███████║███████║",
    "██║╚██╔╝██║██╔══██║██╔══██║██╔══██║",
    "██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██║",
    "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝",
]

TL, TR, BL, BR, H, V = "\u256D", "\u256E", "\u2570", "\u256F", "\u2500", "\u2502"


class Paint:
    """Colour, degrading honestly: truecolor, then 256, then nothing at all
    when the output is redirected to a file."""

    def __init__(self, enabled):
        self.on = enabled
        self.true = enabled and (
            os.environ.get("COLORTERM", "") in ("truecolor", "24bit"))

    def _rgb(self, r, g, b, code):
        if not self.on:
            return ""
        if self.true:
            return f"\033[38;2;{r};{g};{b}m"
        return f"\033[38;5;{code}m"

    def amber(self):  return self._rgb(0xF5, 0x9E, 0x0B, 214)
    def sand(self):   return self._rgb(0xF2, 0xDD, 0xB4, 223)
    def slate(self):  return self._rgb(0x6B, 0x7E, 0x90, 245)
    def red(self):    return self._rgb(0xEF, 0x44, 0x44, 203)
    def reset(self):  return RESET if self.on else ""

    def w(self, s, colour):
        return f"{colour}{s}{self.reset()}" if self.on else s


def open_page(port):
    """Open the page, on whichever platform this is."""
    url = f"http://127.0.0.1:{port}"
    for cmd in (["open", url], ["xdg-open", url], ["termux-open-url", url]):
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass
    return False


def quiet_flask():
    """Werkzeug shouts a red block about development servers. Read as
    broken, it makes every visit feel like an incident. This binds to
    127.0.0.1 only, so the warning's actual concern does not apply."""
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    try:
        import flask.cli
        flask.cli.show_server_banner = lambda *a, **k: None
    except Exception:
        pass
    try:
        import werkzeug.serving as ws
        ws._log = lambda *a, **k: None
    except Exception:
        pass


def hms(sec):
    if sec is None or sec < 0:
        return "\u2014"
    sec = int(sec)
    h, m = sec // 3600, (sec % 3600) // 60
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {sec % 60}s"
    return f"{sec}s"


class Console:
    """The dashboard. Redraws in place; never scrolls."""

    def __init__(self, paint, port, snapshot):
        self.p = paint
        self.port = port
        self.snapshot = snapshot          # callable -> dict
        self.prev_lines = 0
        self.msg = {"text": "", "kind": "", "until": 0.0}

    def flash(self, text, kind=""):
        self.msg.update(text=text, kind=kind, until=time.time() + 4)

    def width(self):
        try:
            return max(46, min(shutil.get_terminal_size().columns, 100))
        except Exception:
            return 60

    def panel(self, title, rows, w):
        p = self.p
        inner = w - 2
        t = f" {title} "
        top = TL + H + p.w(t, p.amber()) + H * max(0, inner - len(t) - 1) + TR
        out = [top]
        for r in rows:
            body = r
            if vlen(body) > inner - 2:
                body = body[:inner - 2]
            pad = max(0, inner - 1 - vlen(body))
            out.append(V + " " + body + " " * pad + V)
        out.append(BL + H * inner + BR)
        return out

    def lines(self):
        p = self.p
        w = self.width()
        out = []

        for row in LOGO:
            out.append(p.w(row, p.amber()))
        out.append("")
        out.append(p.w("  Maha Transcribe", p.sand())
                   + p.w("   \u00b7   " + f"http://127.0.0.1:{self.port}", p.slate()))
        out.append("")

        s = self.snapshot() if self.snapshot else {}
        ffmpeg_line = (p.w("ffmpeg ready", p.sand()) if s.get("ffmpeg")
                      else p.w("ffmpeg NOT found, file picker cannot convert", p.red()))
        rows = [
            p.w(f"version {s.get('version', '?')}", p.sand())
            + p.w("   \u00b7   up " + hms(s.get("uptime")), p.slate()),
            p.w(f"{s.get('requests', 0)} request(s) answered", p.slate()),
            ffmpeg_line,
        ]
        if s.get("optimized"):
            rows.append(p.w(f"{s['optimized']} file(s) optimized, "
                            f"{s.get('saved_mb', 0):.1f} MB saved", p.slate()))
        out += self.panel("STATUS", rows, w)
        out.append("")

        keys = [("Q", "quit"), ("O", "open page"), ("R", "restart"), ("C", "redraw")]
        krow = "   ".join(
            f"{p.w('[' + k + ']', p.amber())} {p.w(v, p.sand())}"
            for k, v in keys)
        out += self.panel("KEYS", [krow], w)

        if self.msg["text"] and time.time() < self.msg["until"]:
            colour = p.red() if self.msg["kind"] == "err" else p.amber()
            out.append("  " + p.w(self.msg["text"][:w - 4], colour))
        else:
            out.append("")
        return out

    def render(self):
        lines = self.lines()
        buf = []
        if self.prev_lines:
            buf.append(f"\033[{self.prev_lines}A")
        for ln in lines:
            buf.append("\033[2K" + ln + "\n")
        sys.stdout.write("".join(buf))
        sys.stdout.flush()
        self.prev_lines = len(lines)


def is_interactive():
    return sys.stdout.isatty() and sys.stdin.isatty()


def run(app, host, port, snapshot=None, note=None):
    """Serve, with the console if there is a terminal to draw it on.

    Returns "quit" or "restart".
    """
    quiet_flask()

    if note and not is_interactive():
        print(note, flush=True)
    if not is_interactive():
        print(f"Maha Transcribe \u2014 http://127.0.0.1:{port}", flush=True)
        app.run(host=host, port=port, threaded=True, debug=False,
                use_reloader=False)
        return "quit"

    import select
    import termios
    import tty

    threading.Thread(
        target=lambda: app.run(host=host, port=port, threaded=True,
                               debug=False, use_reloader=False),
        daemon=True).start()

    paint = Paint(True)
    con = Console(paint, port, snapshot)
    if note:
        con.msg.update(text=note, kind="", until=time.time() + 90)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    sys.stdout.write("\033[?25l\033[2J\033[H")

    threading.Timer(1.0, open_page, args=(port,)).start()

    action = "quit"
    try:
        tty.setcbreak(fd)
        while True:
            con.render()
            r, _, _ = select.select([fd], [], [], 0.5)
            if not r:
                continue
            ch = os.read(fd, 1).decode(errors="ignore").lower()
            if ch in ("q", "\x03", "\x04"):
                action = "quit"
                break
            if ch == "r":
                action = "restart"
                break
            if ch == "o":
                ok = open_page(port)
                con.flash("opening the browser" if ok
                          else "no way to open a browser from here",
                          "" if ok else "err")
            elif ch == "c":
                con.prev_lines = 0
                sys.stdout.write("\033[2J\033[H")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()

    if action == "quit":
        print(paint.w("  stopped.", paint.slate()))
    return action
