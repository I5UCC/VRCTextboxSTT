from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from config import LANGUAGE_TO_KEY
from time import time
from helper import log, get_absolute_path
import shutil
import huggingface_hub as hub
import os
from glob import glob
import traceback

class TranslationHandler(object):
    def __init__(self, cache_path, model_size="small", device_str="cuda:0"):
        self.device = device_str
        self.cache_path = cache_path
        self.model = M2M100ForConditionalGeneration
        self.tokenizer = M2M100Tokenizer
        self.model_path = ""
        self.download_model(model_size)
        self.load_model()

    def load_model(self):
        self.model = M2M100ForConditionalGeneration.from_pretrained(self.model_path).to(self.device)
        self.tokenizer = M2M100Tokenizer.from_pretrained(self.model_path)

    def translate(self, text, from_language, to_language):
        t = time()
        self.tokenizer.src_lang = LANGUAGE_TO_KEY[from_language]
        encoded = self.tokenizer(text, return_tensors="pt").to(self.device)
        generated_tokens = self.model.generate(**encoded, forced_bos_token_id=self.tokenizer.get_lang_id(LANGUAGE_TO_KEY[to_language])).to(self.device)
        translation_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        text = ' '.join(translation_text)
        log.info(f"Translation took {time() - t} seconds")
        return text

    def download_model(self, size="small"):
        match size.lower():
            case "large":
                self.model_path = get_absolute_path("cachem2m100-large/", self.cache_path)
                repo_id = "facebook/m2m100_1.2B"
            case _:
                self.model_path = get_absolute_path("cache/m2m100-small/", self.cache_path)
                repo_id = "facebook/m2m100_418M"

        if not os.path.exists(self.model_path):
            dirname = hub.snapshot_download(repo_id)
        else:
            return

        try:
            os.mkdir(self.model_path)
        except FileExistsError:
            return
        except Exception:
            log.fatal("Failed to create cache directory: ")
            log.error(traceback.format_exc())

        g = glob(dirname + "\\*")
        for f in g:
            temp = os.path.realpath(f)
            filename = f[f.rindex("\\"):]
            shutil.move(temp, self.model_path + filename)

        shutil.rmtree(os.path.join(os.path.expanduser("~"), ".cache\huggingface"))