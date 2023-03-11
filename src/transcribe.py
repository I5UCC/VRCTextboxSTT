import whisper
import torch
from helper import get_absolute_path
import sys

class TranscribeHandler(object):
    def __init__(self, config, script_path) -> None:
        self.config = config
        self.whisper_model = self.config["model"].lower()
        self.language = self.config["language"].lower()
        if self.language == "":
            self.language = None
        elif "large" not in self.whisper_model and self.language == "english" and ".en" not in self.whisper_model:
            self.whisper_model = self.whisper_model + ".en"
        self.task = "translate" if self.config["translate_to_english"] and self.language != "english" else "transcribe"
        print(f"Using model: {self.whisper_model} for language: {self.language} ({self.task}) ")

        self.device = "cpu" if bool(self.config["use_cpu"]) or not torch.cuda.is_available() else "cuda"
        self.use_cpu = True if str(self.device) == "cpu" else False

        self.model: whisper.Whisper = whisper.load_model(self.whisper_model, download_root=get_absolute_path("whisper_cache/", script_path), in_memory=True, device=self.device)
        
        print("Testing model... (This may take a while)", file=sys.stderr)

    def test(self):
        self.transcribe(torch.zeros(256))
    
    def transcribe(self, audio, last_tokens=[]) -> tuple:
        """
        Transcribes the given audio data using the model and returns the text and the tokens.
        :param torch_audio: The audio data as an np array/torch tensor.
        :param last_tokens: The last tokens of the previous transcription.
        """

        _options = {"without_timestamps": True, "prompt": last_tokens, "task": self.task}
        _result = self.model.transcribe(audio, fp16=not self.use_cpu, language=self.language, **_options)

        _text = _result['text']
        _tokens = []
        for segment in _result['segments']:
            _tokens += segment['tokens']

        return (_text, _tokens)
