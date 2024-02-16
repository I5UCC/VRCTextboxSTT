from helper import get_best_compute_type, measure_time
from shutil import rmtree
from config import translator_config, LANGUAGE_TO_KEY, TRANSLATE_MODELS
from ctranslate2.converters import TransformersConverter
import ctranslate2
import transformers
import os
import json
import traceback
import torch
import logging

log = logging.getLogger(__name__)


class TranslationHandler(object):
    """
    Handles translation of text using a pre-trained translation model.

    Args:
        cache_path (str): The path to the cache directory.
        source_language (str): The source language for translation.
        translator_conf (translator_config): The configuration object for the translator.

    Attributes:
        cache_path (str): The path to the cache directory.
        translator_config (translator_config): The configuration object for the translator.
        from_language (str): The source language for translation.
        to_language (str): The target language for translation.
        device (str): The device (CPU or GPU) used for translation.
        device_index (int): The index of the device used for translation.
        model (str): The pre-trained translation model.
        compute_type (str): The compute type used for translation.
        model_path (str): The path to the pre-trained translation model.
        translator (ctranslate2.Translator): The translation engine.
        tokenizer (transformers.AutoTokenizer): The tokenizer for the translation model.

    """

    def __init__(self, cache_path, source_language, translator_conf: translator_config):
        self.cache_path = cache_path
        self.translator_config = translator_conf
        self.from_language = LANGUAGE_TO_KEY[source_language]
        self.to_language = LANGUAGE_TO_KEY[self.translator_config.language]
        if torch.cuda.is_available():
            self.device = self.translator_config.device.type
            self.device_index = self.translator_config.device.index
        else:
            self.device = "cpu"
            self.device_index = 0
        self.model = TRANSLATE_MODELS[self.translator_config.model]
        self.compute_type = self.translator_config.device.compute_type if self.translator_config.device.compute_type else get_best_compute_type(self.device, self.device_index)
        self.model_path = f"{self.cache_path}{self.model.split('/')[1]}-ct2-{self.compute_type}/"
        self.download_model()
        self.load_model()

    def load_model(self) -> None:
        """
        Loads the pre-trained translation model and tokenizer.
        """
        self.translator = ctranslate2.Translator(self.model_path, device=self.device, device_index=self.device_index, compute_type=self.compute_type, inter_threads=self.translator_config.device.num_workers, intra_threads=self.translator_config.device.cpu_threads)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_path)
        self.tokenizer.src_lang = self.from_language

    @measure_time
    def translate(self, text) -> str:
        """
        Translates the given text from the source language to the target language.

        Args:
            text (str): The text to be translated.

        Returns:
            str: The translated text.
        """
        source = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text))
        target_prefix = [self.tokenizer.lang_code_to_token[self.to_language]]
        results = self.translator.translate_batch([source], target_prefix=[target_prefix])
        target = results[0].hypotheses[0][1:]
        text_trans = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(target))

        if self.translator_config.show_original:
            return self.translator_config.format.replace("{1}", text).replace("{2}", text_trans)
        else:
            return text_trans

    def download_model(self) -> None:
        """
        Downloads and converts the pre-trained translation model if necessary.
        """
        try:
            _converter = TransformersConverter(self.model, copy_files=["generation_config.json", "sentencepiece.bpe.model", "special_tokens_map.json", "tokenizer_config.json", "vocab.json"])
            _converter.convert(self.model_path, force=False, quantization=self.compute_type)
            j: dict = json.load(open(self.model_path + "config.json"))
            j.update({"model_type": "m2m_100"})
            json.dump(j, open(self.model_path + "config.json", "w"), indent=4)
            rmtree(os.path.join(os.path.expanduser("~"), ".cache\huggingface"))
        except RuntimeError:
            log.info("Model already exists, skipping conversion.")
        except FileNotFoundError:
            log.error("Model Cache doesnt exist.")
            log.error(traceback.format_exc())
        except Exception:
            log.error("Unknown error loading model: ")
            log.error(traceback.format_exc())
