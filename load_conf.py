# load_conf.py (was config.py)

import toml

_config = toml.load("config.toml")

# Audio Settings
SAMPLERATE = _config["audio"]["samplerate"]
CHANNELS = _config["audio"]["channels"]
INPUT_DEVICE = _config["audio"]["input_device"]
BLOCKSIZE = _config["audio"]["blocksize"]
LISTEN_DURATION = _config["audio"]["listen_duration"]
TEMP_AUDIO_DIR = _config["audio"]["temp_audio_dir"]

# Vad settings
VAD_CUTOFF_LEVEL = _config["vad"].get("cutoff_level", 15)
VAD_CUTOFF_LENGTH = _config["vad"].get("cutoff_length", 3.0)

# Whisper Model
WHISPER_MODEL_PATH = _config["whisper"]["model_path"]

# LLM Settings
LLM_CHAT_MODE = _config["llm"].get("chat_mode", False)
LLM_SYSTEM_PROMPT = _config["llm"]["system_prompt"]
LLM_IDENTITY = _config["llm"]["identity"]
LLM_SCENE = _config["llm"]["scene"]
LLM_API_URL = _config["llm"]["url"]
LLM_TEMPERATURE = _config["llm"]["temperature"]
LLM_MAX_TOKENS = _config["llm"]["max_tokens"]
LLM_STOP = _config["llm"]["stop"]

# Memory Settings
MEMORY_ENABLED = _config["memory"]["enabled"]
MEMORY_CHAR_LIMIT = _config["memory"]["char_limit"]

# Piper (TTS)
PIPER_EXECUTABLE = _config["piper"]["executable"]
PIPER_VOICE_PATH = _config["piper"]["voice_path"]
PIPER_CONFIG_PATH = _config["piper"]["config_path"]

# TTS Output Settings
OUTPUT_WAV = _config["tts"]["output_wav"]

# Controls
EXIT_KEY = _config["controls"]["exit_key"]
INJECT_KEY = _config["controls"]["inject_key"]
THEN_KEY = _config["controls"]["then_key"]

