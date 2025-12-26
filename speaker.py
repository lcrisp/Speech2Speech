import os
import re
import json
import wave
import subprocess
from piper.voice import PiperVoice
from piper.config import SynthesisConfig

def _which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(":"):
        fp = os.path.join(p, cmd)
        if os.path.isfile(fp) and os.access(fp, os.X_OK):
            return fp
    return None

class Speaker:
    """
    Piper speaker with:
      - speed control via SynthesisConfig(length_scale=...)
      - deterministic punctuation pauses by inserting silence frames
    """

    def __init__(self, voice_path: str, config_path: str, output_wav: str):
        self.voice_path = voice_path
        self.config_path = config_path
        self.output_wav = output_wav

        # TUNE THESE:
        # Bigger = slower. Typical usable range: 1.3 .. 2.3
        self.length_scale = 2.0
        # Pause lengths (ms)
        self.pause_comma_ms = 220
        self.pause_sentence_ms = 550

        print("[Speaker] Loading Piper voice...")
        self.voice = PiperVoice.load(self.voice_path, config_path=self.config_path)
        self.syn = SynthesisConfig(length_scale=self.length_scale)
        print(f"[Speaker] Loaded. length_scale={self.length_scale}")

        # Get sample rate for inserting silence
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.sample_rate = int(cfg.get("audio", {}).get("sample_rate", 22050))

    def _chunks(self, text: str):
        """Split text into (chunk, punct) to pause on punctuation."""
        t = re.sub(r"\s+", " ", (text or "").strip())
        if not t:
            return []
        out = []
        buf = []
        for ch in t:
            buf.append(ch)
            if ch in [",", ".", "!", "?", ";", ":"]:
                out.append(("".join(buf).strip(), ch))
                buf = []
        tail = "".join(buf).strip()
        if tail:
            out.append((tail, ""))
        return out

    def _append_silence(self, wf: wave.Wave_write, ms: int):
        frames = int(self.sample_rate * ms / 1000)
        wf.writeframes(b"\x00\x00" * frames)  # int16 mono silence

    def speak(self, text: str) -> str:
        os.makedirs(os.path.dirname(self.output_wav) or ".", exist_ok=True)

        parts = self._chunks(text)
        if not parts:
            print("[Speaker] Nothing to speak.")
            return self.output_wav

        print(f"[Speaker] Speaking {len(parts)} chunk(s). SR={self.sample_rate}Hz")

        with wave.open(self.output_wav, "wb") as wf:
            first = True
            for chunk, punct in parts:
                if not chunk:
                    continue

                # Let piper set wav format on first write, then append frames for subsequent chunks
                self.voice.synthesize_wav(
                    chunk,
                    wf,
                    syn_config=self.syn,
                    set_wav_format=first
                )
                first = False

                if punct == ",":
                    self._append_silence(wf, self.pause_comma_ms)
                elif punct in [".", "!", "?", ";", ":"]:
                    self._append_silence(wf, self.pause_sentence_ms)

        size = os.path.getsize(self.output_wav)
        print(f"[Speaker] Wrote WAV: {self.output_wav} ({size} bytes)")
        if size <= 44:
            print("[Speaker] WARNING: WAV looks empty (header-only).")
            return self.output_wav

        # Playback
        if _which("paplay"):
            subprocess.run(["paplay", self.output_wav], check=False)
        elif _which("aplay"):
            subprocess.run(["aplay", self.output_wav], check=False)
        else:
            print("[Speaker] No paplay/aplay found; audio not played.")

        return self.output_wav
