# MAHA_TRANSCRIBE_TERMUX_TERMINAL

Runs [maha_transcribe.html](./maha_transcribe.html) from a small local
**Flask** server, on Android via Termux or on any macOS/Linux terminal, and
exposes it as one shell command: `transcribe`.

The server exists mainly because Android browsers refuse microphone access
(`getUserMedia`) on a plain `file://` page. Serving the same file over
`http://127.0.0.1` makes it a secure context, so recording works.

Built to the same house pattern as `GDRIVE_DOWNLOADER_FLASK_MACOS`: a port
picker that never fails to start, a local-only request guard instead of a
password, and the same terminal dashboard, all in a private virtual
environment so nothing here touches your system Python.

## Install — Termux (Android)

```bash
curl -fsSL https://raw.githubusercontent.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL/main/install-termux.sh | bash
```

Optional, so `transcribe` can auto-open your browser instead of you copying
the link by hand: install the **Termux:API** app (F-Droid or Play Store),
then `pkg install termux-api`.

## Install — macOS / Linux terminal

```bash
curl -fsSL https://raw.githubusercontent.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL/main/install-terminal.sh | bash
```

Both installers build a private virtual environment (`.venv`) inside the
install folder and put Flask in it, so nothing is installed system-wide.

## Usage

```bash
transcribe            # start the app: a live terminal dashboard, browser opens on its own
transcribe 9000        # start on a specific port instead of the default
transcribe-update      # git pull the latest version, refresh dependencies, then exit
```

While `transcribe` is running, the terminal shows a small dashboard —
version, address, uptime, request count — with four keys:

```
[Q] quit    [O] open page    [R] restart    [C] redraw
```

If the default port (8420) is already busy, the server tries the next ports
up on its own and prints whichever one it actually used, so `transcribe`
never just fails because something else is running — including another
copy of itself, which it recognises by name rather than guessing.

## What's in here

| file | purpose |
|---|---|
| `maha_transcribe.html` | the app itself, single file, no keys inside |
| `app.py` | the Flask server: one route, hands the browser the app |
| `portpick.py` | finds a free port, never refuses to start |
| `localguard.py` | refuses requests that didn't really come from 127.0.0.1 |
| `console.py` | the terminal dashboard `transcribe` draws while it runs |
| `requirements.txt` | Flask, installed into a private `.venv` |
| `transcribe` | starts the app |
| `transcribe-update` | pulls the latest version and refreshes dependencies |
| `install-termux.sh` | one-line installer for Termux |
| `install-terminal.sh` | one-line installer for a regular terminal |

## Updating

`transcribe-update` does `git pull` in the install directory, then
reinstalls `requirements.txt` into the existing `.venv` in case a dependency
changed. Since your API keys live only in your browser's storage, never in
this repository, an update never touches them.

## API keys

`maha_transcribe.html` holds **no keys of any kind**. On first use, open the
gear icon and import your keys under **api keys**, either by pasting a note
or picking a file — the app finds keys by shape (`sk-ant-`, `gsk_`, `AQ.`,
or 32-hex for AssemblyAI) and ignores the surrounding prose. Keys are stored
only in that browser's `localStorage`, never in this repository, never
committed, never sent anywhere but the provider they belong to.

Each provider keeps a small ring of keys with automatic fallback: a key that
gets rate-limited rests and comes back on its own, a key that gets revoked
is set aside permanently, and a genuinely broken request (not the key's
fault) stops rather than burning through the whole ring. You can see every
key masked, test one by hand, delete it, or revive one you know is good
again, all from Settings.

Because there is nothing secret in the file, **this repo can safely stay
public.**

## Why a Flask server and not just a static file

Two things it does that opening the file directly cannot:

- **Microphone access.** `file://` pages are not a secure context on
  Android, so `getUserMedia` is refused outright. `http://127.0.0.1` is.
- **Loopback-only by design.** `localguard.py` checks the request's Host
  header on every request, so a request that arrived by DNS rebinding —
  a hostname pointed at 127.0.0.1 after the fact, so the connection is
  local but the browser sent someone else's domain name — is refused with
  a plain 403 rather than quietly served.
