import os
import torch
import time
from helper import get_best_compute_type, log
from faster_whisper import WhisperModel
from ctranslate2.converters import TransformersConverter
from shutil import rmtree
from config import whisper_config, device_config, MODELS, LANGUAGE_TO_KEY
import traceback

class TranscribeHandler(object):
    def __init__(self, config_whisper: whisper_config, config_device: device_config, cache_path, translate) -> None:
        self.whisper_config: whisper_config = config_whisper
        self.device_config: device_config = config_device
        self.cache_path = cache_path
        self.whisper_model = self.whisper_config.model if "/" in self.whisper_config.model else MODELS[self.whisper_config.model]
        self.is_openai_model = True if "openai" in self.whisper_model else False
        self.language = None

        if self.whisper_config.language:
            self.language = LANGUAGE_TO_KEY[self.whisper_config.language]

        if self.is_openai_model and "large" not in self.whisper_model and self.language == "en" and ".en" not in self.whisper_model:
            self.whisper_model = self.whisper_model + ".en"

        self.task = "translate" if translate and self.language != "english" and self.is_openai_model else "transcribe"

        if torch.cuda.is_available():
            self.device = self.device_config.type
            self.device_index = self.device_config.index
        else:
            self.device = "cpu"
            self.device_index = 0

        self.compute_type = self.device_config.compute_type if self.device_config.compute_type else get_best_compute_type(self.device, self.device_index)
        
        log.info(f"Using model: {self.whisper_model} for language: {self.language} ({self.task}) - {self.compute_type}")
        
        self.use_cpu = True if str(self.device) == "cpu" else False
        self.model_path = self.load_model(self.whisper_model, self.compute_type, self.is_openai_model)

        self.device_name = torch.cuda.get_device_name(self.device_index) if self.device == "cuda" else "CPU"
        
        self.model: WhisperModel = WhisperModel(self.model_path, self.device, self.device_index, self.compute_type, self.device_config.cpu_threads, self.device_config.num_workers)

    def transcribe(self, audio) -> str:
        """
        Transcribes the given audio data using the model and returns the text and the tokens.

        :param torch_audio: The audio data as an np array/torch tensor.
        :param last_tokens: The last tokens of the previous transcription.
        """

        _text = ""
        try:
            segments, _ = self.model.transcribe(audio, beam_size=5, language=self.language, word_timestamps=False, without_timestamps=True, task=self.task)
            _text = "".join([segment.text for segment in segments])
        except Exception:
            log.error("Error transcribing: ")
            log.error(traceback.format_exc())
            return None

        log.info("Transcription: " + _text)

        return _text

    def load_model(self, model_name: str = "openai/whisper-base.en", quantization = "float32", download_tokenizer = True):
        """
        Loads a Transformer model from the given path and converts it to a ctranslate2 model.

        :param model_name: The name of the model to load.
        :param quantization: The quantization to use for the model.
        :return: The path to the ctranslate2 model.
        """
        try:
            model_split = model_name.split('/')
            _model_path = f"{self.cache_path}{model_split[0]}-{model_split[1]}-ct2-{quantization}"
            _converter = TransformersConverter(model_name, copy_files=["tokenizer.json"] if download_tokenizer else None)
            _converter.convert(_model_path, force=False, quantization=quantization)

            rmtree(os.path.join(os.path.expanduser("~"), ".cache\huggingface"))
        except RuntimeError:
            log.info("Model already exists, skipping conversion.")
        except FileNotFoundError:
            log.error("Model Cache doesnt exist.")
            log.error(traceback.format_exc())
        except Exception:
            log.error("Unknown error loading model: ")
            log.error(traceback.format_exc())

        return _model_path
