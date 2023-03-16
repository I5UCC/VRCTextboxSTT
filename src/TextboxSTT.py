import os
import sys
import logging
from helper import LogToFile, loadfont, get_absolute_path, play_sound, get_config


VERSION = "v1.0.0-Alpha"
LOGFILE = get_absolute_path('out.log', __file__)
CONFIG_PATH = get_absolute_path('config.json', __file__)
DEFAULT_CONFIG_PATH = get_absolute_path("resources/default.json", __file__)
CONFIG = get_config(CONFIG_PATH, DEFAULT_CONFIG_PATH)


open(LOGFILE, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = LogToFile(log, logging.INFO, LOGFILE)
sys.stderr = LogToFile(log, logging.ERROR, LOGFILE)


if os.name == 'nt':
    loadfont(get_absolute_path("resources/CascadiaCode.ttf", __file__))


import threading
import time
import keyboard
import re
import psutil
from ui import MainWindow, SettingsWindow
from osc import OscHandler
from browsersource import OBSBrowserSource
from ovr import OVRHandler
from listen import ListenHandler
from transcribe import TranscribeHandler


osc: OscHandler = None
ovr: OVRHandler = None
listen: ListenHandler = None
transcriber: TranscribeHandler = None
browsersource: OBSBrowserSource = OBSBrowserSource(CONFIG, get_absolute_path('resources/obs_source.html', __file__))
use_kat: bool = True
use_textbox: bool = True
use_both: bool = True
curr_time: float = 0.0
pressed: bool = False
holding: bool = False
held: bool = False
thread_process: threading.Thread = threading.Thread()
config_ui: SettingsWindow = None
config_ui_open: bool = False
enter_pressed: bool = False
initialized: bool = False


def init():
    """Initialize the application."""

    global main_window
    global config_ui
    global osc
    global use_textbox
    global use_kat
    global use_both
    global transcriber
    global ovr
    global initialized
    global browsersource
    global listen

    initialized = False

    config_ui = SettingsWindow(CONFIG, CONFIG_PATH)

    osc = OscHandler(CONFIG["osc_ip"], CONFIG["osc_port"], CONFIG["osc_ip"], CONFIG["osc_server_port"])
    use_textbox = bool(CONFIG["use_textbox"])
    use_kat = bool(CONFIG["use_kat"])
    use_both = bool(CONFIG["use_both"])

    main_window.set_status_label("LOADING WHISPER MODEL", "orange")
    transcriber = TranscribeHandler(CONFIG, __file__)
    main_window.set_status_label(f"LOADED \"{transcriber.whisper_model}\"", "orange")

    # load the speech recognizer
    listen = ListenHandler(CONFIG)

    # Initialize OpenVR
    main_window.set_status_label("INITIALIZING OVR", "orange")
    if ovr:
        ovr.shutdown()
    ovr = OVRHandler(CONFIG, __file__)
    if ovr.initialized:
        main_window.set_status_label("INITIALZIED OVR", "green")
    else:
        main_window.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "orange")

    # Start Flask server
    if CONFIG["enable_obs_source"]:
        if browsersource.start():
            main_window.set_status_label("INITIALIZED FLASK SERVER", "green")
            print(f"Flask server started on 127.0.0.1:{CONFIG['obs_source']['port']}")
        else:
            main_window.set_status_label("COULDNT INITIALIZE FLASK SERVER, CONTINUING WITHOUT OBS SOURCE", "orange")

    main_window.set_conf_label(CONFIG["osc_ip"], CONFIG["osc_port"], CONFIG["osc_server_port"], ovr.initialized, transcriber.device, transcriber.whisper_model)
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")
    initialized = True


def sound(filename):
    """Plays a sound file."""

    if CONFIG["audio_feedback"]:
        play_sound(filename, __file__)


def replace_emotes(text):
    """Replaces emotes in the text with the configured emotes."""

    if not text:
        return None

    if CONFIG["emotes"] is None:
        return text

    for i in range(len(CONFIG["emotes"])):
        word = CONFIG["emotes"][str(i)]
        if word == "":
            continue
        tmp = re.compile(word, re.IGNORECASE)
        text = tmp.sub(osc.emote_keys[i], text)

    return text


def replace_words(text):
    """Replaces words in the text with the configured replacements."""

    if not text:
        return None

    text = text.strip()
    if not CONFIG["enable_word_replacements"] or CONFIG["word_replacements"] == {}:
        return text

    for key, value in CONFIG["word_replacements"].items():
        tmp = re.compile(key, re.IGNORECASE)
        text = tmp.sub(value, text)

    text = re.sub(' +', ' ', text)
    return text


def set_typing_indicator(state: bool, textfield: bool = False):
    """Sets the typing indicator for the Chatbox and KAT."""

    global use_textbox
    global use_kat
    global use_both
    global osc

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.set_textbox_typing_indicator(state)
    if use_kat and osc.isactive and not textfield:
        osc.set_kat_typing_indicator(state)


def clear_chatbox():
    """Clears the Chatbox, KAT and Overlay."""

    global use_textbox
    global use_kat
    global use_both
    global osc
    global ovr
    global browsersource

    if browsersource:
        browsersource.setText("")
    main_window.clear_textfield()
    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.clear_chatbox(CONFIG["mode"] == 0)
    if use_kat and osc.isactive:
        osc.clear_kat()
    main_window.set_text_label("- No Text -")
    ovr.set_overlay_text("")


def populate_chatbox(text, cutoff: bool = False, is_textfield: bool = False):
    """Populates the Chatbox, KAT and Overlay with the given text."""

    global main_window
    global use_textbox
    global use_kat
    global use_both
    global osc
    global ovr
    global browsersource

    text = replace_words(text)
    if browsersource:
        browsersource.setText(text)

    if not text:
        return

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.set_textbox_text(text, cutoff, CONFIG["mode"] == 0 and not is_textfield)

    if use_kat and osc.isactive:
        _kat_text = text
        if CONFIG["enable_emotes"]:
            _kat_text = replace_emotes(_kat_text)
        osc.set_kat_text(_kat_text, cutoff)

    if cutoff:
        text = text[-osc.textbox_charlimit:]
    else:
        text = text[:osc.textbox_charlimit]

    main_window.set_text_label(text)
    ovr.set_overlay_text(text)

    set_typing_indicator(False)


def process_forever():
    """Processes audio data from the data queue until the user cancels the process by pressing the button again."""

    global main_window
    global pressed
    global config_ui_open
    global listen
    global transcriber

    sound("listen")

    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")

    listen.start_listen_background()

    _time_last = time.time()
    while True:
        if config_ui_open:
            break

        if pressed:
            _time_last = time.time()
            _held = False
            while pressed:
                if time.time() - _time_last > CONFIG["hold_time"]:
                    _held = True
                    break
                time.sleep(0.05)
            if _held:
                main_window.set_status_label("CLEARED", "#00008b")
                sound("clear")
                clear_chatbox()
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            _torch_audio = listen.raw_to_np(_last_sample)

            _text = transcriber.transcribe(_torch_audio)

            _time_last = time.time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time.time() - _time_last > CONFIG["pause_threshold"]:
            print(_text)
            _last_sample = bytes()

        time.sleep(0.05)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()
    time.sleep(1)


def process_loop():
    """Processes audio data from the data queue and transcribes it until the user stops talking."""

    global listen
    global main_window
    global pressed
    global listen

    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    sound("listen")

    listen.start_listen_background()

    _time_last = time.time()
    while True:
        if pressed:
            _time_last = time.time()
            _held = False
            while pressed:
                if time.time() - _time_last > CONFIG["hold_time"]:
                    _held = True
                    break
                time.sleep(0.05)
            if _held:
                main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
                sound("clear")
                clear_chatbox()
                break
            elif _last_sample == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                sound("timeout")
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            _np_audio = listen.raw_to_np(_last_sample)

            _text = transcriber.transcribe(_np_audio)

            _time_last = time.time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time.time() - _time_last > CONFIG["pause_threshold"]:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            print(_text)
            sound("finished")
            break
        elif _last_sample == bytes() and time.time() - _time_last > CONFIG["timeout_time"]:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            sound("timeout")
            break
        time.sleep(0.05)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()
    time.sleep(0.1)


def process_once():
    """Process a single input and return the transcription."""

    global main_window
    global pressed
    global listen

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    sound("listen")
    _np_audio = listen.listen_once()
    if _np_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        sound("timeout")
        set_typing_indicator(False)
    else:
        sound("donelisten")
        set_typing_indicator(True)
        print(_np_audio)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _trans = transcriber.transcribe(_np_audio)
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                sound("timeout")
            elif _trans:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_trans)
                sound("finished")
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                sound("timeout")
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            sound("timeout")

    set_typing_indicator(False)
    main_window.set_button_enabled(True)


def get_trigger_state():
    """Returns the state of the trigger, either from the keyboard or the ovr action"""

    global ovr

    if ovr.initialized and ovr.get_ovraction_bstate():
        return True
    else:
        return keyboard.is_pressed(CONFIG["hotkey"])


def handle_input():
    """Handles all input from the user"""

    global thread_process
    global held
    global holding
    global pressed
    global curr_time
    global config_ui_open

    pressed = get_trigger_state()

    if not thread_process.is_alive() and CONFIG["mode"] == 2 and not config_ui_open:
        thread_process = threading.Thread(target=process_forever)
        thread_process.start()
    elif thread_process.is_alive() or config_ui_open:
        return
    elif pressed and not holding and not held:
        holding = True
        curr_time = time.time()
    elif pressed and holding and not held:
        holding = True
        if time.time() - curr_time > CONFIG["hold_time"]:
            clear_chatbox()
            main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
            sound("clear")
            held = True
            holding = False
    elif not pressed and holding and not held:
        held = True
        holding = False
        thread_process = threading.Thread(target=process_loop if CONFIG["mode"] else process_once)
        thread_process.start()
    elif not pressed and held:
        held = False
        holding = False


def entrybox_enter_event(text):
    """Handles the enter event for the textfield."""
    global main_window
    global enter_pressed

    enter_pressed = True
    if text:
        populate_chatbox(text, False, True)
        sound("finished")
        main_window.clear_textfield()
    else:
        clear_chatbox()
        sound("clear")


def textfield_keyrelease(text):
    """Handles the key release event for the textfield."""
    global osc
    global use_kat
    global enter_pressed

    if not enter_pressed:
        if len(text) > osc.textbox_charlimit:
            main_window.textfield.delete(osc.textbox_charlimit, len(text))
            main_window.textfield.icursor(osc.textbox_charlimit)
        _is_text_empty = text == ""
        set_typing_indicator(not _is_text_empty, True)
        if _is_text_empty:
            clear_chatbox()
        else:
            populate_chatbox(text, False, True)

    enter_pressed = False


def main_window_closing():
    """Handles the closing of the main window."""
    global main_window
    global config_ui
    global use_kat
    global osc
    global browsersource

    print("Closing...")
    try:
        osc.stop()
    except Exception as e:
        print(e)
    try:
        main_window.on_closing()
    except Exception as e:
        print(e)
    try:
        config_ui.on_closing()
    except Exception as e:
        print(e)
    try:
        browsersource.stop()
    except Exception as e:
        print(e)


def settings_closing(save=False):
    """Handles the closing of the settings menu. If save is True, saves the settings and restarts the program."""

    global osc
    global config_ui
    global config_ui_open
    global browsersource

    if save:
        try:
            if config_ui_open:
                config_ui.save()
                config_ui.on_closing()
        except Exception as e:
            print("Error saving settings: " + str(e))
        try:
            ovr.destroy_overlay()
        except Exception as e:
            print("Error destroying overlay: " + str(e))
        try:
            osc.stop()
        except Exception as e:
            print("Error stopping osc: " + str(e))
        try:
            init()
        except Exception as e:
            print(e)
            main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO out.log for more info on the error", "red")
    else:
        config_ui.on_closing()
        main_window.set_status_label("SETTINGS NOT SAVED - WAITING FOR INPUT", "#00008b")

    main_window.set_button_enabled(True)
    config_ui_open = False


def open_settings():
    """Opens the settings menu"""

    global main_window
    global config_ui
    global config_ui_open

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = SettingsWindow(CONFIG, CONFIG_PATH)
    config_ui.button_refresh.configure(command=determine_energy_threshold)
    config_ui.btn_save.configure(command=(lambda: settings_closing(True)))
    config_ui.tkui.protocol("WM_DELETE_WINDOW", settings_closing)
    main_window.set_button_enabled(False)
    config_ui.open()


def determine_energy_threshold():
    """Determines the energy threshold for the microphone to use for speech recognition"""

    global config_ui
    global listen

    config_ui.set_energy_threshold("Be quiet for 5 seconds...")
    config_ui.set_energy_threshold(listen.get_energy_threshold())


def check_ovr():
    global initialized
    global ovr
    global config_ui_open

    if not initialized or config_ui_open or ovr.initialized or (os.name == 'nt' and "vrmonitor.exe" not in (p.name() for p in psutil.process_iter())):
        return

    print("check ovr")
    settings_closing(True)


main_window = MainWindow(VERSION)
try:
    init()
except Exception as e:
    print(e)
    main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO out.log for more info on the error", "red")

main_window.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
main_window.textfield.bind("<Return>", (lambda event: entrybox_enter_event(main_window.textfield.get())))
main_window.textfield.bind("<KeyRelease>", (lambda event: textfield_keyrelease(main_window.textfield.get())))
main_window.btn_settings.configure(command=open_settings)
main_window.create_loop(7000, check_ovr)
main_window.create_loop(50, handle_input)
main_window.open()
