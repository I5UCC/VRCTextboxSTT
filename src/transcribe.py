import os
import torch
from helper import get_best_compute_type, measure_time
from faster_whisper import WhisperModel, __version__ as whisper_version
from ctranslate2 import __version__ as ctranslate2_version
from ctranslate2.converters import TransformersConverter
from shutil import rmtree
from config import whisper_config, vad_config, ct2_device_config, WHISPER_MODELS, LANGUAGE_TO_KEY
import traceback
import logging
from numpy import zeros, ndarray, float32

log = logging.getLogger(__name__)

class TranscribeHandler(object):
    """
    Handles the transcription of audio using the Whisper model.

    Args:
        config_whisper (whisper_config): The configuration for the Whisper model.
        config_vad (vad_config): The configuration for the Voice Activity Detection (VAD).
        cache_path (str): The path to the cache directory.
        translate (bool): Flag indicating whether translation is enabled.

    Attributes:
        config_whisper (whisper_config): The configuration for the Whisper model.
        config_vad (vad_config): The configuration for the Voice Activity Detection (VAD).
        device_config (ct2_device_config): The device configuration for the Whisper model.
        cache_path (str): The path to the cache directory.
        whisper_model (str): The path or name of the Whisper model.
        is_openai_model (bool): Flag indicating whether the Whisper model is an OpenAI model.
        language (str): The language code for the transcription.
        task (str): The task type for the Whisper model.
        device (str): The device type for model inference.
        device_index (int): The index of the device.
        compute_type (str): The compute type for the model.
        use_cpu (bool): Flag indicating whether CPU is used for model inference.
        model_path (str): The path to the loaded model.
        device_name (str): The name of the device used for model inference.
        model (WhisperModel): The Whisper model instance.

    Methods:
        transcribe: Transcribes the audio and returns the transcribed text.
        load_model: Loads the Whisper model.
    """

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
        if "distil" in self.whisper_model and self.language != "en":
            log.warning("Distil models only support English. Overriding language to English.")
            self.language = "en"

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
        
        self.use_cpu = True if str(self.device) == "cpu" else False
        self.model_path = self.load_model(self.whisper_model, self.compute_type, self.is_openai_model)

        self.device_name = torch.cuda.get_device_name(self.device_index) if self.device == "cuda" else "CPU"

        if self.device_config.flash_attention and "30" not in self.device_name:
            log.warning("Flash attention is only supported on Ampere GPUs and above. Disabling flash attention.")
            self.device_config.flash_attention = False
        self.model: WhisperModel = WhisperModel(self.model_path, self.device, self.device_index, self.compute_type, self.device_config.cpu_threads, self.device_config.num_workers, flash_attention=self.device_config.flash_attention)

        log.debug(f"Using model: {self.whisper_model} for language: {self.language} ({self.task}) - {self.compute_type}")
        log.debug(f"Language: {self.language}")
        log.debug(f"Task: {self.task}")
        log.debug(f"Device: {self.device} ({self.device_index}) - {self.device_name}")
        log.debug(f"Compute Type: {self.compute_type}")
        log.debug(f"VAD Enabled: {self.config_vad.enabled}")
        log.debug(f"VAD Parameters: {self.config_vad.parameters.__dict__}")

    @measure_time
    def transcribe(self, audio: ndarray = zeros(100000, dtype=float32)) -> str:
        """
        Transcribes the given audio and returns the transcribed text.

        Args:
            audio: The audio input for transcription.

        Returns:
            str: The transcribed text.
        """
        _text = ""
        try:
            segments, _ = self.model.transcribe(audio, temperature=0.0, language=self.language, word_timestamps=False, without_timestamps=True, task=self.task, vad_filter=self.config_vad.enabled, vad_parameters=self.config_vad.parameters.__dict__)
            # With high no_speech_prob and modest avg_logprob, seems to be likely hallucinations
            # Code adapted from the TaSTT project
            for s in segments:
                if s.no_speech_prob > 0.6 and s.avg_logprob < -0.5:
                    log.warning(f"Skipping possible hallucination: {s.text}\n" +
                                f"with no_speech_prob: {s.no_speech_prob}\n" +
                                f"and avg_logprob: {s.avg_logprob}\n" +
                                "case 1")
                    continue
                if s.no_speech_prob > 0.15 and s.avg_logprob < -0.7:
                    log.warning(f"Skipping possible hallucination: {s.text}\n" +
                                f"with no_speech_prob: {s.no_speech_prob}\n" +
                                f"and avg_logprob: {s.avg_logprob}\n" +
                                "case 2")
                    continue
                _text += s.text
        except Exception:
            log.error("Error transcribing: ")
            log.error(traceback.format_exc())
            return None

        return _text.strip()

    def load_model(self, model_name: str = "openai/whisper-base.en", quantization = "float32", download_tokenizer = True) -> str:
        """
        Loads the Whisper model.

        Args:
            model_name (str): The name of the model to load.
            quantization: The quantization type for the model.
            download_tokenizer (bool): Flag indicating whether to download the tokenizer.

        Returns:
            str: The path to the loaded model.
        """
        try:
            model_split = model_name.split('/')
            _model_path = f"{self.cache_path}{model_split[0]}-{model_split[1]}-ct2-{quantization}"
            copy_files = ["preprocessor_config.json", "tokenizer.json"]
            _converter = TransformersConverter(model_name, copy_files=copy_files)
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
