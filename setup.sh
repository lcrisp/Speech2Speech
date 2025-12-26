#!/usr/bin/env bash
set -euo pipefail

# =========================
# S2S-Chain-MM Setup Script
# Idempotent: safe to rerun
# =========================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$REPO_ROOT/app"
VENV_DIR="$APP_DIR/.venv312"
LOG_DIR="$REPO_ROOT/setup_logs"
LOG="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== S2S-Chain-MM setup start: $(date) ==="
echo "Repo: $REPO_ROOT"
echo "App : $APP_DIR"
echo "Log : $LOG"
echo

# ---------- helpers ----------
need_cmd() { command -v "$1" >/dev/null 2>&1; }
fail() { echo; echo "ERROR: $*"; echo "See log: $LOG"; exit 1; }

# ---------- Step 1: OS deps ----------
echo "== Step 1/6: Install system packages =="

if ! need_cmd apt-get; then
  fail "This script expects Debian/Ubuntu with apt-get."
fi

sudo apt-get update

sudo apt-get install -y \
  python3 python3-venv python3-dev \
  ffmpeg \
  portaudio19-dev \
  libasound2-dev \
  pkg-config \
  curl \
  ca-certificates

echo

# ---------- Step 2: uv ----------
echo "== Step 2/6: Ensure uv is installed =="

if need_cmd uv; then
  echo "uv: $(uv --version)"
else
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  need_cmd uv || fail "uv install failed (PATH issue?). Try: export PATH=\$HOME/.local/bin:\$PATH"
  echo "uv: $(uv --version)"
fi

echo

# ---------- Step 3: Create venv (Python 3.12) ----------
echo "== Step 3/6: Create/refresh venv (.venv312) =="

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Prefer Python 3.12 if uv can obtain it; otherwise fallback to system python3.
# If you *must* enforce 3.12 strictly, remove the fallback and fail instead.
if uv python list 2>/dev/null | grep -q "3.12"; then
  echo "Using uv-managed Python 3.12"
  uv venv --python 3.12 "$VENV_DIR"
else
  echo "Python 3.12 not listed by uv; using system python3 (may be 3.12 anyway)."
  uv venv --python python3 "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -V
echo

# ---------- Step 4: Install Python deps ----------
echo "== Step 4/6: Install Python dependencies =="

# CPU-only, stable stack
uv pip install -U pip

uv pip install \
  toml requests numpy \
  sounddevice soundfile pynput \
  onnxruntime piper-tts \
  openai-whisper

echo
python - <<'PY'
import sys
print("Python OK:", sys.version)
import whisper
import onnxruntime
import piper.voice
print("Imports OK: whisper, onnxruntime, piper")
PY
echo

# ---------- Step 5: Validate config + Piper voices ----------
echo "== Step 5/6: Validate config.toml and Piper voice files =="

CONFIG="$APP_DIR/config.toml"
[ -f "$CONFIG" ] || fail "Missing $CONFIG"

python - <<'PY'
import toml, os, sys
cfg = toml.load("config.toml")

p = cfg.get("piper", {})
voice_path  = p.get("voice_path")
config_path = p.get("config_path")

if not voice_path or not config_path:
    print("ERROR: [piper] voice_path/config_path missing in config.toml")
    sys.exit(2)

print("Piper voice_path :", voice_path)
print("Piper config_path:", config_path)

missing = []
for path in (voice_path, config_path):
    if not os.path.isfile(path):
        missing.append(path)

if missing:
    print("\nERROR: Missing Piper files:")
    for m in missing:
        print("  -", m)
    print("\nFix: Put the .onnx and .onnx.json in that location OR update config.toml to match.")
    sys.exit(3)

print("Piper files exist ✅")
PY

echo

# ---------- Step 6: Sanity test: Piper actually produces audio ----------
echo "== Step 6/6: Sanity test Piper synthesis produces non-empty audio =="

python - <<'PY'
from piper.voice import PiperVoice
from piper.config import SynthesisConfig
import toml, wave, os

cfg = toml.load("config.toml")
p = cfg["piper"]

voice = PiperVoice.load(p["voice_path"], config_path=p["config_path"])
syn = SynthesisConfig(length_scale=2.0)

wav_path = "/tmp/s2s_setup_test.wav"
with wave.open(wav_path, "wb") as wf:
    voice.synthesize_wav("Setup complete. Piper is working.", wf, syn_config=syn, set_wav_format=True)

size = os.path.getsize(wav_path)
print("Wrote:", wav_path, "bytes:", size)

if size <= 44:
    raise SystemExit("ERROR: WAV is header-only. Piper is not generating audio.")
PY

if need_cmd paplay; then
  echo "Playing test WAV via paplay..."
  paplay /tmp/s2s_setup_test.wav || true
elif need_cmd aplay; then
  echo "Playing test WAV via aplay..."
  aplay /tmp/s2s_setup_test.wav || true
else
  echo "No paplay/aplay found; skipping playback."
fi

echo
echo "=== Setup finished successfully ==="
echo "Next:"
echo "  cd \"$APP_DIR\""
echo "  source \"$VENV_DIR/bin/activate\""
echo "  python main.py"
echo
echo "Log saved to: $LOG"
