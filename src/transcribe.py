import os
import torch
from helper import get_best_compute_type
from faster_whisper import WhisperModel, __version__ as whisper_version
from ctranslate2 import __version__ as ctranslate2_version
from ctranslate2.converters import TransformersConverter
from shutil import rmtree
from config import whisper_config, vad_config, ct2_device_config, WHISPER_MODELS, LANGUAGE_TO_KEY
import traceback
import logging

log = logging.getLogger(__name__)

class TranscribeHandler(object):
    def __init__(self, config_whisper: whisper_config, config_vad: vad_config, cache_path, translate) -> None:
        self.config_whisper: whisper_config = config_whisper
        self.config_vad: vad_config = config_vad
        self.device_config: ct2_device_config = config_whisper.device
        self.cache_path = cache_path
        self.whisper_model = self.config_whisper.model if "/" in self.config_whisper.model else WHISPER_MODELS[self.config_whisper.model]
        self.is_openai_model = True if "openai" in self.whisper_model else False
        self.language = None

        if self.config_whisper.language:
            self.language = LANGUAGE_TO_KEY[self.config_whisper.language]

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
        log.info("ct2 version: " + ctranslate2_version)
        log.info("whisper version: " + whisper_version)
        log.info("torch version: " + torch.__version__)
        
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
            segments, _ = self.model.transcribe(audio, beam_size=5, temperature=0.0, log_prob_threshold=-0.8, no_speech_threshold=0.6, language=self.language, word_timestamps=False, without_timestamps=True, task=self.task, vad_filter=self.config_vad.enabled, vad_parameters=self.config_vad.parameters.__dict__)
            for s in segments:
                if s.avg_logprob < -0.8 or s.no_speech_prob > 0.6:
                    continue
                _text += s.text
        except Exception:
            log.error("Error transcribing: ")
            log.error(traceback.format_exc())
            return None

        return _text

    def load_model(self, model_name: str = "openai/whisper-base.en", quantization = "float32", download_tokenizer = True):
        """
        Loads a Transformer model from the given path and converts it to a ctranslate2 model.

        :param model_name: The name of the model to load.
        :param quantization: The quantization to use for the model.
        :return: The path to the ctranslate2 model.
        """
        try:
            if "guillaumekln" in model_name:
                model_name = model_name.split("-")[-1].lower()
                model_name = WHISPER_MODELS[model_name]
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
