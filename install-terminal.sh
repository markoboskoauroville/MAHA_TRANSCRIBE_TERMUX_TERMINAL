#!/usr/bin/env bash
# Install Maha Transcribe in a normal macOS or Linux terminal (not Termux).
# Run with:  curl -fsSL https://raw.githubusercontent.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL/main/install-terminal.sh | bash
set -euo pipefail

REPO_URL="https://github.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL.git"
INSTALL_DIR="$HOME/MAHA_TRANSCRIBE_TERMUX_TERMINAL"
BIN_DIR="$HOME/bin"

command -v python3 >/dev/null || { echo "python3 is required, install it first"; exit 1; }
command -v git >/dev/null || { echo "git is required, install it first"; exit 1; }
python3 -c 'import venv' >/dev/null 2>&1 || { echo "python3's venv module is missing, install it first"; exit 1; }

if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "already cloned, pulling latest..."
  cd "$INSTALL_DIR"
  git pull --ff-only
else
  echo "cloning repository..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
echo "building the virtual environment..."
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

chmod +x "$INSTALL_DIR/transcribe" "$INSTALL_DIR/transcribe-update"

mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/transcribe" "$BIN_DIR/transcribe"
ln -sf "$INSTALL_DIR/transcribe-update" "$BIN_DIR/transcribe-update"

echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "$BIN_DIR is not on your PATH yet, add this to your shell profile:"
  echo "  export PATH=\"\$HOME/bin:\$PATH\""
fi
echo "done. commands:"
echo "  transcribe            start the app, Flask serving it locally"
echo "  transcribe-update     pull the latest version and refresh dependencies"
