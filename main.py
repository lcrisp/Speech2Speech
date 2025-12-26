# main.py (corrected imports)

import time
from load_conf import SAMPLERATE, WHISPER_MODEL_PATH, LLM_SYSTEM_PROMPT, LLM_API_URL, MEMORY_ENABLED, MEMORY_CHAR_LIMIT, PIPER_EXECUTABLE, PIPER_VOICE_PATH, OUTPUT_WAV
from vad_recorder import VADRecorder
from listener import Listener
from llm_connector import LLMConnector
from memory_manager import MemoryManager
from speaker import Speaker
from controls import Controls
from load_conf import (
    SAMPLERATE,
    WHISPER_MODEL_PATH,
    LLM_SYSTEM_PROMPT,
    LLM_IDENTITY,
    LLM_SCENE,
    LLM_API_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_STOP,
    MEMORY_ENABLED,
    MEMORY_CHAR_LIMIT,
    PIPER_EXECUTABLE,
    PIPER_VOICE_PATH,
    PIPER_CONFIG_PATH,  # ✅ keep this in the list
    OUTPUT_WAV,
    EXIT_KEY,
    INJECT_KEY,
    THEN_KEY
)



recorder = VADRecorder(SAMPLERATE)
listener = Listener(model_path=WHISPER_MODEL_PATH)
llm = LLMConnector()
memory = MemoryManager(enabled=MEMORY_ENABLED, limit=MEMORY_CHAR_LIMIT)

print("[Debug] Using voice path:", PIPER_VOICE_PATH)
print("[Debug] Using config path:", PIPER_CONFIG_PATH)

speaker = Speaker(PIPER_VOICE_PATH, PIPER_CONFIG_PATH, OUTPUT_WAV)
controls = Controls()

print("\n[System] Assistant is running... Press ESC to exit.\n")

def build_prompt(memory_text, user_text):
    full_prompt = f"{LLM_SYSTEM_PROMPT}\n{memory_text}\nUser: {user_text}\nMaya:"
    return {"prompt": full_prompt, "temperature": 0.7, "max_tokens": 150}

while True:
    if controls.check_exit():
        print("[System] Exit key pressed. Shutting down...")
        break

    wav_path = recorder.record_with_vad()
    if not wav_path:
        continue

    user_text = listener.transcribe(wav_path)
    print(f"[User] {user_text}")

    memory_text = memory.inject_memory(user_text)
    payload = build_prompt(memory_text, user_text)

    reply = llm.query(user_text)
    print(f"[Maya] {reply}")

    speaker.speak(reply)
    time.sleep(1)
