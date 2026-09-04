# MAHA_TRANSCRIBE_TERMUX_TERMINAL

Runs [maha_transcribe.html](./maha_transcribe.html) from a tiny local Python
server, on Android via Termux or on any macOS/Linux terminal, and exposes it
as one shell command: `transcribe`.

The server exists mainly because Android browsers refuse microphone access
(`getUserMedia`) on a plain `file://` page. Serving the same file over
`http://127.0.0.1` makes it a secure context, so recording works.

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

## Usage

```bash
transcribe            # start the app, opens your browser
transcribe 9000        # start on a specific port instead of the default
transcribe-update      # git pull the latest version, then exit
```

If the default port (8420) is already busy, the server tries the next ports
up on its own and prints whichever one it actually used, so `transcribe`
never just fails because something else is running.

## What's in here

| file | purpose |
|---|---|
| `maha_transcribe.html` | the app itself, single file, all API keys hardcoded inside |
| `server.py` | local HTTP server with automatic port fallback |
| `transcribe` | starts the app |
| `transcribe-update` | pulls the latest version from this repo |
| `_repo_dir.sh` | shared helper the two commands above source |
| `install-termux.sh` | one-line installer for Termux |
| `install-terminal.sh` | one-line installer for a regular terminal |

## Updating

Since your API keys live inside `maha_transcribe.html` itself, every update
to the app is a new commit to this repo. `transcribe-update` just does
`git pull` in the install directory, so the keys already on your phone stay
put unless the update itself changes them.

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
