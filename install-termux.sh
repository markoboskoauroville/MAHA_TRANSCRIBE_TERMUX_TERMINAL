#!/data/data/com.termux/files/usr/bin/bash
# Install Maha Transcribe in Termux.
# Run with:  curl -fsSL https://raw.githubusercontent.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL/main/install-termux.sh | bash
set -euo pipefail

REPO_URL="https://github.com/markoboskoauroville/MAHA_TRANSCRIBE_TERMUX_TERMINAL.git"
INSTALL_DIR="$HOME/MAHA_TRANSCRIBE_TERMUX_TERMINAL"
BIN_DIR="$PREFIX/bin"

echo "installing dependencies (python, git)..."
pkg update -y
pkg install -y python git

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
python -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

chmod +x "$INSTALL_DIR/transcribe" "$INSTALL_DIR/transcribe-update"

mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/transcribe" "$BIN_DIR/transcribe"
ln -sf "$INSTALL_DIR/transcribe-update" "$BIN_DIR/transcribe-update"

echo ""
echo "done. commands now available anywhere in Termux:"
echo "  transcribe            start the app, Flask serving it locally"
echo "  transcribe-update     pull the latest version and refresh dependencies"
echo ""
echo "for transcribe to auto-open your browser, also install the Termux:API app"
echo "from F-Droid/Play Store and run:  pkg install termux-api"
