import sys
import os
sys.path.append(os.path.dirname(__file__))
DEBUG = len(sys.argv) == 1
from time import sleep, time
from listen import ListenHandler
from transcribe import TranscribeHandler
from browsersource import OBSBrowserSource
from translate import TranslationHandler
from helper import get_absolute_path, replace_words
import keyboard
from config import config_struct
import numpy as np

def main():
    global enabled, listen
    
    if DEBUG:
        CACHE_PATH = get_absolute_path('cache/', __file__)
        CONFIG_PATH = get_absolute_path('config.json', __file__)
    else:
        CACHE_PATH = get_absolute_path('../cache/', __file__)
        CONFIG_PATH = get_absolute_path('../config.json', __file__)
    config: config_struct = config_struct.load(CONFIG_PATH)

    if config.listener.pause_threshold < 3.0:
        config.listener.pause_threshold = 3.0
    if config.listener.timeout_time < 5.0:
        config.listener.timeout_time = 5.0
    if config.text_timeout < config.listener.timeout_time:
        config.text_timeout = config.listener.timeout_time * 2

    listen = ListenHandler(config.listener)
    transcriber = TranscribeHandler(config.whisper, config.vad, CACHE_PATH, config.translator.language == "english")
    transcriber.transcribe(np.zeros(100000, dtype=np.float32))
    translator: TranslationHandler = None
    if config.translator.language and config.translator.language != config.whisper.language and transcriber.task == "transcribe":
        translator = TranslationHandler(CACHE_PATH, config.whisper.language, config.translator)
    browsersource = OBSBrowserSource(config.obs, get_absolute_path('resources/obs_source.html', __file__), CACHE_PATH)
    browsersource.start()

    phrase_timeout = config.listener.timeout_time
    clear_timeout = config.text_timeout
    max_transciption_time = config.whisper.max_transciption_time
    max_samples = config.whisper.max_samples
    cutoff_buffer = config.whisper.cutoff_buffer
    toggle_hotkey = config.hotkey
    energy_threshold = config.listener.energy_threshold

    phrase_time = None
    last_sample = bytes()
    enabled = True
    cleared = True
    phrase_end = False
    time_taken = 0.0
    append = False
    last_text = ""
    sentence_end = False
    first_run = True

    def toggle_enabled():
        global enabled, listen

        enabled = not enabled
        if enabled:
            listen.start_listen_background()
            print("------------------------ ENABLED -------------------------")
        else:
            listen.stop_listen_background()
            print("------------------------ DISABLED ------------------------")

    keyboard.add_hotkey(toggle_hotkey, toggle_enabled)

    if not energy_threshold:
        print("Adjusting for ambient noise. Please wait a moment and be silent.")
        listen.rec.energy_threshold = listen.get_energy_threshold()

    print("---------------- OBS Whisper Transcriber -----------------")
    print("Press {} to toggle listening.".format(toggle_hotkey))
    print("Press Ctrl+C to exit, or close the console window.")
    print("----------------------------------------------------------")
    print("device:\t\t\t{}".format(config.whisper.device.__dict__))
    print("phrase_timeout:\t\t{}".format(phrase_timeout))
    print("clear_timeout:\t\t{}".format(clear_timeout))
    print("max_transciption_time:\t{}".format(max_transciption_time))
    print("max_samples:\t\t{}".format(max_samples))
    print("cutoff_buffer:\t\t{}".format(cutoff_buffer))
    print("energy_threshold:\t{}".format(energy_threshold))
    print("vad:\t\t\t{}".format(config.vad.enabled))
    print()
    print(transcriber.device_name, transcriber.whisper_model, transcriber.compute_type)

    listen.start_listen_background()

    print("------------------------ LISTENING -----------------------")
    while True:
        try:
            time_last = time()

            if not listen.data_queue.empty():
                browsersource.finished = False
                cleared = False
                phrase_end = False
                
                try:
                    while not listen.data_queue.empty():
                        data = listen.data_queue.get()
                        last_sample += data
                    pre = time()
                    torch_audio = listen.raw_to_np(last_sample)

                    print("----------------------------------------------------------")
                    text = transcriber.transcribe(torch_audio)
                    if not text:
                        continue

                    if translator:
                        text = translator.translate(text)
                    if append and text:
                        text = last_text + text

                    time_taken = time() - pre
                    print(f"Time taken:\t{time_taken:.5f}s (max: {max_transciption_time}s)")
                    print(f"bytes:\t\t{len(last_sample)}\ntext_length:\t{len(text)}")
                    if config.wordreplacement.enabled:
                        text = replace_words(text, config.wordreplacement.list)
                        text = replace_words(text, config.wordreplacement.base_replacements)
                    browsersource.setText(text)
                    print("- " + text if text else "No text found")

                    first_run = False
                    sentence_end = text and text[-1] in {".", "!", "?"}
                    if sentence_end and not first_run and (len(last_sample) > max_samples or time_taken > max_transciption_time):
                        print("------------------------ CUTOFF ----------------------")
                        last_text = text + " "
                        append = True
                        last_sample = last_sample[-cutoff_buffer:]
                except Exception as e:
                    print(e)
                phrase_time = time()
            elif not cleared and phrase_time and time_last - phrase_time > clear_timeout:
                cleared = True
                browsersource.setText("")
                print("------------------------- CLEARED ------------------------")
            elif not phrase_end and phrase_time and time_last - phrase_time > phrase_timeout:
                append = False
                phrase_end = True
                browsersource.finished = True
                last_sample = bytes()
                print("------------------------ NEW PHRASE ----------------------")

            sleep(0.1)
        except KeyboardInterrupt:
            listen.stop_listen_background()
            browsersource.stop()
            break

if __name__=='__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
