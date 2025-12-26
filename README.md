S2S-Chain-MM

Local Speech-to-Speech Pipeline (STT → LLM → TTS)

This project implements a fully local speech-to-speech conversational loop:

Microphone
   ↓
Voice Activity Detection (VAD)
   ↓
Speech-to-Text (STT – Whisper, CPU)
   ↓
LLM (LM Studio, local HTTP API)
   ↓
Text-to-Speech (Piper, ONNX, CPU)
   ↓
Audio Playback


The system is designed to:

run entirely locally

avoid CUDA / cuDNN / GPU dependency traps

be reproducible on modern Debian systems

survive Python version churn

1. Why this exists

This codebase was originally part of a longer experimental chain and was later resurrected with minimal documentation. During reconstruction, several important realities became clear:

Python 3.13 breaks many ML wheels (notably ctranslate2)

faster-whisper introduces fragile native dependencies

Piper’s API changed and silently produces empty WAVs if misused

CPU-only, pure-Python paths are vastly more reliable for long-lived setups

This README documents the known-good architecture that actually works.

2. What currently works (known-good state)

✔ Continuous microphone capture with VAD
✔ CPU Whisper transcription
✔ LLM inference via LM Studio
✔ Piper TTS producing real audio
✔ Human-paced speech with punctuation pauses
✔ Playback via PipeWire / PulseAudio / ALSA

No CUDA. No GPU. No silent failures.

3. Repository layout
S2S-chain-MM/
├── app/
│   ├── main.py              # Orchestrator loop
│   ├── vad_recorder.py      # Microphone + VAD
│   ├── listener.py          # Whisper STT (CPU)
│   ├── llm_connector.py     # LM Studio HTTP client
│   ├── speaker.py           # Piper TTS + playback (patched)
│   ├── config.toml          # Runtime configuration
│   ├── run.sh               # Canonical launch script
│   └── .venv312/            # Python 3.12 virtual environment
│
├── TTS/
│   └── piper_voices/        # ONNX voices + JSON configs
│
└── README.md

4. Python & environment strategy (important)
⚠️ Do NOT use system Python blindly

Python 3.13 breaks ctranslate2

Debian repositories may not provide older minor versions

✅ Solution used here

Python 3.12

Virtual environment created via uv

CPU-only ML stack

This avoids:

native ABI mismatches

cuDNN hard crashes

silent ONNX failures

5. Virtual environment setup (reproducible)
# install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

cd app
uv venv --python 3.12 .venv312
source .venv312/bin/activate


Install dependencies:

uv pip install \
  toml requests numpy \
  sounddevice soundfile pynput \
  onnxruntime piper-tts \
  openai-whisper


Note:
faster-whisper is deliberately not used. It depends on ctranslate2, which is fragile on new Python versions.

6. Configuration (config.toml)
Piper (TTS)
[piper]
voice_path  = "/workspace/TTS/piper_voices/en_GB-vctk-medium.onnx"
config_path = "/workspace/TTS/piper_voices/en_GB-vctk-medium.onnx.json"


Use absolute paths. Relative paths caused repeated failures.

Whisper (STT)

Whisper is CPU-only and loaded in listener.py:

model: base

no CUDA

stable and predictable

LLM (LM Studio)

llm_connector.py expects LM Studio running in server mode, typically:

http://127.0.0.1:1234/v1/chat/completions


Model choice is up to you.

7. The Speaker implementation (critical detail)
Why Piper “worked” but produced no sound

Piper’s API exposes:

synthesize() → returns audio chunks (does NOT write WAV)

synthesize_wav() → writes audio to WAV

Calling the wrong method results in:

valid WAV header

0 audio frames

total silence

Correct usage (implemented in speaker.py)

Uses synthesize_wav(...)

Reads sample rate from voice JSON

Inserts explicit silence frames for punctuation

Uses SynthesisConfig(length_scale=...) to slow speech

8. Speech pacing & punctuation

Human-friendly speech is achieved by two mechanisms:

1. Global speed control
self.length_scale = 2.0


Typical range:

1.6 – moderate slowdown

2.0 – clear & calm

2.3 – very deliberate

2. Deterministic pauses

Text is split into chunks on punctuation:

Punctuation	Pause
,	~220 ms
. ! ?	~550 ms

This is far more reliable than relying on model prosody alone.

9. Running the system
Always use the launcher
cd app
./run.sh


run.sh ensures:

correct venv

CUDA disabled

consistent runtime

10. Debugging tips (lessons learned)
If you get silence

Check WAV size (> 44 bytes)

Ensure synthesize_wav() is used

Confirm sample rate matches voice config

If Python exits instantly

Run with:

python main.py 2>&1 | tee crash.log


Native aborts ≠ Python exceptions

If CUDA errors appear

Something pulled in a GPU wheel

Remove it and reinstall CPU-only versions

11. Future improvements (deliberately postponed)

Optional faster-whisper with pinned Python & wheels

Streaming TTS instead of full WAV

GUI / tray integration

Wake-word detection

Text normalization before TTS

All possible — none required for stability.

12. Final note to future maintainers

This project looks simpler than it is.

Most of the complexity is not in the code, but in:

Python version compatibility

ML wheel behavior

silent failure modes

If something breaks after an upgrade:

Check Python version

Check whether a GPU-enabled wheel was installed

Verify Piper is producing non-empty WAVs

Start there. Always.# Speech2Speech
