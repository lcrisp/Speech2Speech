import whisper

class Listener:
    def __init__(self, model_path="base"):
        self.model = whisper.load_model(model_path)

    def transcribe(self, wav_path: str) -> str:
        result = self.model.transcribe(wav_path)
        return result.get("text", "").strip()
