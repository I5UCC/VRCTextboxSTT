import sys
import os
sys.path.append(os.path.dirname(__file__))
DEBUG = len(sys.argv) == 1
from time import sleep, time
from listen import ListenHandler
from transcribe import TranscribeHandler
from ovr import OVRHandler
from translate import TranslationHandler
from helper import get_absolute_path, replace_words
import keyboard
from config import config_struct
import numpy as np
import re
import traceback
from ui import SettingsWindow
import subprocess
from logger import force_single_instance

def restart(save: bool = False) -> None:
    """
    Restarts the program.
    """
    global settings_window
    if save:
        settings_window.save()
    
    settings_window.on_closing()
    subprocess.Popen([sys.executable, *sys.argv])
    sys.exit(0)

def open_settings(config, config_path) -> None:
    global settings_window

    def get_coordinates():
        return (50, 50)

    settings_window = SettingsWindow(config, config_path, __file__, get_coordinates, get_coordinates)
    settings_window.tkui.protocol("WM_DELETE_WINDOW", restart)
    settings_window.btn_save.config(command=lambda: restart(True))
    settings_window.open()

def main():
    global enabled, listen, settings_window

    CACHE_PATH = get_absolute_path('../cache/', __file__)
    CONFIGS_PATH = get_absolute_path('../configs/', __file__)

    try:
        os.mkdir(CONFIGS_PATH)
    except FileExistsError:
        pass
    except Exception:
        print("Failed to create cache directory: ")
        print(traceback.format_exc())

    CONFIG_PATH = os.path.join(CONFIGS_PATH, "obs_only.json")
    if not os.path.exists(CONFIG_PATH):
        config_struct.save(config_struct(), CONFIG_PATH)
    config: config_struct = config_struct.load(CONFIG_PATH)

    replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.list.items()}
    base_replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.base_replacements.items()}

    if config.listener.pause_threshold < 3.0:
        config.listener.pause_threshold = 3.0
    if config.listener.timeout_time < 5.0:
        config.listener.timeout_time = 5.0
    if config.text_timeout < config.listener.timeout_time:
        config.text_timeout = config.listener.timeout_time * 2

    listen = ListenHandler(config.listener)
    transcriber = TranscribeHandler(config.whisper, config.vad, CACHE_PATH, config.translator.language == "english")
    transcriber.transcribe()
    translator: TranslationHandler = None
    if config.translator.language and config.translator.language != config.whisper.language and transcriber.task == "transcribe":
        translator = TranslationHandler(CACHE_PATH, config.whisper.language, config.translator)
    font_language = config.whisper.language if not config.translator.language else config.translator.language
    ovr = OVRHandler(config.overlay, __file__, font_language, DEBUG)
    while not ovr.is_running():
        ovr.init()
        sleep(3)
    if ovr.overlay_font != font_language:
        ovr.set_overlay_font(font_language)

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
    print()
    print("Press F12 to open settings.")

    listen.start_listen_background()

    print("------------------------ LISTENING -----------------------")
    while True:
        try:
            if keyboard.is_pressed("F12"):
                open_settings(config, CONFIG_PATH)
            time_last = time()

            if not listen.data_queue.empty():
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
                        text = replace_words(text, replacement_dict)
                        text = replace_words(text, base_replacement_dict)

                    if not text:
                        continue

                    ovr.set_overlay_text(text)
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
                ovr.set_overlay_text("")
                print("------------------------- CLEARED ------------------------")
            elif not phrase_end and phrase_time and time_last - phrase_time > phrase_timeout:
                append = False
                phrase_end = True
                last_sample = bytes()
                print("------------------------ NEW PHRASE ----------------------")

            sleep(0.1)
        except KeyboardInterrupt:
            listen.stop_listen_background()
            ovr.shutdown()
            break

if __name__=='__main__':
    if not DEBUG:
        force_single_instance()
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
