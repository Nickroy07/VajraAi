#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[VAJRA AI] Installing backend dependencies"
python -m pip install --upgrade pip
pip install -r "$ROOT_DIR/backend/requirements.txt" -r "$ROOT_DIR/backend/requirements-dev.txt"

echo "[VAJRA AI] Installing dashboard dependencies"
cd "$ROOT_DIR/dashboard"
npm install

echo "[VAJRA AI] Installing mobile dependencies"
cd "$ROOT_DIR/mobile"
npm install

echo "Setup complete."
