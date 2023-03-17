import os
import torch
import time
from helper import get_absolute_path, get_best_compute_type, MODELS, LANGUAGE_TO_KEY
from faster_whisper import WhisperModel
from ctranslate2.converters import TransformersConverter
from shutil import rmtree

class TranscribeHandler(object):
    def __init__(self, config, script_path) -> None:
        self.config = config
        self.script_path = script_path
        self.whisper_model = MODELS[self.config["model"]]
        self.language = None
        
        if self.config["language"]:
            self.language = LANGUAGE_TO_KEY[self.config["language"]]

        if "large" not in self.whisper_model and self.language == "en" and ".en" not in self.whisper_model and "openai" in self.whisper_model:
            self.whisper_model = self.whisper_model + ".en"

        self.task = "translate" if self.config["translate_to_english"] and self.language != "english" else "transcribe"
        print(f"Using model: {self.whisper_model} for language: {self.language} ({self.task}) ")
        
        if self.config["device"] == "cpu":
            self.device_index = 0
            self.device = "cpu"
        else:
            _device_str = self.config["device"].split(":")
            self.device_index = int(_device_str[1])
            self.device = _device_str[0] if torch.cuda.is_available() else "cpu"
            self.device_index = int(_device_str[1])
        
        print(get_best_compute_type(self.device, self.device_index))
        self.compute_type = self.config["compute_type"] if self.config["compute_type"] else get_best_compute_type(self.device, self.device_index)
        self.use_cpu = True if str(self.device) == "cpu" else False
        self.model_path = self.load_model(self.whisper_model, self.compute_type)

        self.device_name = torch.cuda.get_device_name(self.device_index) if self.device == "cuda" else "CPU"
        
        self.model: WhisperModel = WhisperModel(self.model_path, self.device,self.device_index, self.compute_type, self.config["cpu_threads"], self.config["num_workers"])

    def transcribe(self, audio) -> tuple:
        """
        Transcribes the given audio data using the model and returns the text and the tokens.

        :param torch_audio: The audio data as an np array/torch tensor.
        :param last_tokens: The last tokens of the previous transcription.
        """

        pre = time.time()
        with torch.no_grad():
            segments, _ = self.model.transcribe(audio, beam_size=5, language=self.language, without_timestamps=True, task=self.task)
        post = time.time()

        print("Transcription took {:.5f} seconds.".format(post - pre))

        _text = ""
        for segment in segments:
            _text += segment.text

        print("Transcription: ", _text)

        return _text
    
    def load_model(self, model_name: str = "openai/whisper-base.en", quantization = "float32"):
        """
        Loads a Transformer model from the given path and converts it to a ctranslate2 model.

        :param model_name: The name of the model to load.
        :param quantization: The quantization to use for the model.
        :return: The path to the ctranslate2 model.
        """
        _model_path = get_absolute_path("whisper_cache/" + model_name.split("/")[1], self.script_path) + "-ct2" + "-" + quantization
        _converter = TransformersConverter(model_name, copy_files=["tokenizer.json"])
        try:
            _converter.convert(_model_path, force=False, quantization=quantization)

            rmtree(os.path.join(os.path.expanduser("~"), ".cache\huggingface"))
        except RuntimeError:
            print("Model already exists, skipping conversion.")
        except FileNotFoundError:
            print("Model Cache doesnt exist.")
        except Exception as e:
            print("Unknown error loading model: ", str(e))

        return _model_path
