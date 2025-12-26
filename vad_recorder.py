# vad_recorder.py (hardened VAD — no cutoff until voice is heard)

import sounddevice as sd
import numpy as np
import soundfile as sf
import tempfile
import time
from load_conf import SAMPLERATE, VAD_CUTOFF_LEVEL, VAD_CUTOFF_LENGTH

class VADRecorder:
    def __init__(self, samplerate=SAMPLERATE, chunk_duration=0.1, max_duration=15.0):
        self.samplerate = samplerate
        self.chunk_duration = chunk_duration
        self.max_duration = max_duration
        self.cutoff_threshold = (VAD_CUTOFF_LEVEL / 100.0) * 32768  # based on int16 range
        self.silence_duration = VAD_CUTOFF_LENGTH
        self.grace_period = 3.0  # seconds before silence logic activates

    def record_with_vad(self):
        print("🎤 Recording... Speak now!")

        num_silent_chunks = 0
        silence_chunks_required = int(self.silence_duration / self.chunk_duration)
        max_chunks = int(self.max_duration / self.chunk_duration)
        grace_chunks = int(self.grace_period / self.chunk_duration)
        chunk_samples = int(self.chunk_duration * self.samplerate)

        heard_voice = False
        recording = []

        with sd.InputStream(samplerate=self.samplerate, channels=1, dtype="int16") as stream:
            for i in range(max_chunks):
                chunk, _ = stream.read(chunk_samples)
                energy = np.sqrt(np.mean(np.square(chunk.astype(np.float32))))
                print(f"[VAD] Chunk {i} energy: {energy:.2f}")  # debug output
                recording.append(chunk)

                if energy > self.cutoff_threshold:
                    if not heard_voice:
                        print("🎙️ Voice detected — start of message.")
                    heard_voice = True
                    num_silent_chunks = 0

                elif heard_voice:
                    if i > grace_chunks:
                        num_silent_chunks += 1
                        if num_silent_chunks >= silence_chunks_required:
                            print("🛑 Sustained low volume. Ending recording.")
                            break
                else:
                    continue  # haven't heard voice yet; ignore cutoff logic

        full_recording = np.concatenate(recording, axis=0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            sf.write(tmp_wav.name, full_recording, self.samplerate)
            print(f"✅ Saved recording: {tmp_wav.name}")
            return tmp_wav.name
