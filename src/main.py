import sys
from helper import LogToFile, get_absolute_path, force_single_instance

force_single_instance()
# Log to file before importing other modules
CACHE_PATH = get_absolute_path('cache/', __file__)
OUT_FILE_LOGGER = LogToFile(CACHE_PATH)
sys.stdout = OUT_FILE_LOGGER
sys.stderr = OUT_FILE_LOGGER

import traceback
import os
import re
from threading import Thread
from time import time, sleep
from keyboard import is_pressed
from ui import MainWindow, SettingsWindow
from osc import OscHandler
from browsersource import OBSBrowserSource
from ovr import OVRHandler
from listen import ListenHandler
from transcribe import TranscribeHandler
from translate import TranslationHandler
from config import config_struct, audio
from pydub import AudioSegment
from helper import loadfont, log
from torch.cuda import is_available
import winsound
import copy

CONFIG_PATH = get_absolute_path('config.json', __file__)

main_window: MainWindow = None
config: config_struct = None
osc: OscHandler = None
ovr: OVRHandler = None
listen: ListenHandler = None
transcriber: TranscribeHandler = None
translator: TranslationHandler = None
browsersource: OBSBrowserSource = None
timeout_time: float = 0.0
finished: bool = False
curr_time: float = 0.0
pressed: bool = False
holding: bool = False
held: bool = False
thread_process: Thread = Thread()
config_ui: SettingsWindow = None
config_ui_open: bool = False
enter_pressed: bool = False
initialized: bool = False


def init():
    """Initialize the application."""

    global config
    global main_window
    global osc
    global transcriber
    global translator
    global ovr
    global initialized
    global browsersource
    global listen

    modify_audio_files(config.audio_feedback.__dict__.copy())

    # Initialize ListenHandler
    if not listen:
        listen = ListenHandler(config.listener)
    else:
        listen.set_config(config.listener)

    # Initialize OpenVR
    if not ovr:
        ovr = OVRHandler(config.overlay, __file__)
    if OVRHandler.is_running():
        ovr.init()
    if ovr.initialized:
        main_window.set_status_label("INITIALZIED OVR", "green")
    else:
        main_window.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "orange")
    
    # Initialize OSC Handler
    if not osc:
        osc = OscHandler(copy.deepcopy(config.osc))
    elif osc.osc_ip != config.osc.ip or osc.osc_port != config.osc.client_port or osc.osc_server_port != config.osc.server_port:
        restart()

    # Start Flask server
    if not browsersource:
        browsersource = OBSBrowserSource(config.obs, get_absolute_path('resources/obs_source.html', __file__))
    if config.obs.enabled and not browsersource.running:
        if browsersource.start():
            main_window.set_status_label("INITIALIZED FLASK SERVER", "green")
            log.info(f"Flask server started on 127.0.0.1:{config.obs.port}")
        else:
            main_window.set_status_label("COULDNT INITIALIZE FLASK SERVER, CONTINUING WITHOUT OBS SOURCE", "orange")
    elif not config.obs.enabled and browsersource.running:
        restart()

    # Temporarily output to text label for download progress.
    OUT_FILE_LOGGER.set_ui_output(main_window.loading_status)
    main_window.set_status_label("LOADING WHISPER MODEL", "orange")
    if not transcriber:
        transcriber = TranscribeHandler(copy.deepcopy(config.whisper), CACHE_PATH, config.translator.language == "english")
    elif config.whisper != transcriber.whisper_config:
        restart()
    main_window.set_status_label(f"LOADED \"{transcriber.whisper_model}\"", "orange")

    # Initialize TranslationHandler
    if config.translator.language and config.translator.language != config.whisper.language and transcriber.task == "transcribe":
        main_window.set_status_label("LOADING TRANSLATION MODEL", "orange")
        if not translator:
            translator = TranslationHandler(CACHE_PATH, config.whisper.language, copy.deepcopy(config.translator))
        elif config.translator != translator.translator_config:
            restart()
    elif translator:
        restart()
    OUT_FILE_LOGGER.remove_ui_output()
    
    main_window.set_text_label("- No Text -")
    main_window.set_conf_label(config.osc.ip, config.osc.client_port, config.osc.server_port, ovr.initialized, transcriber.device_name, transcriber.whisper_model, transcriber.compute_type, config.whisper.device.cpu_threads, config.whisper.device.num_workers)
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")
    main_window.set_button_enabled(True)

    initialized = True


def modify_audio_files(audio_dict):
    del audio_dict["enabled"]
    for key in audio_dict:
        try:
            _tmp_audio: audio = audio_dict[key]
            _segment = AudioSegment.from_wav(get_absolute_path(f"resources/{_tmp_audio.file}", __file__))
            _segment = _segment + _tmp_audio.gain
            _segment.export(get_absolute_path(f"cache/{_tmp_audio.file}", __file__), format="wav")
        except Exception:
            log.error(f"Failed to modify audio file \"{_tmp_audio.file}\": ")
            log.error(traceback.format_exc())


def play_sound(au: audio):
    """Plays a sound file."""

    global config

    if not config.audio_feedback.enabled:
        return

    _file = get_absolute_path(f"cache/{au.file}", __file__)
    if not os.path.isfile(_file):
        log.info(f"Sound file \"{_file}\" does not exist.")
        return

    try:
        winsound.PlaySound(_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        log.error(f"Failed to play sound \"{_file}\": ")
        log.error(traceback.format_exc())


def replace_emotes(text):
    """Replaces emotes in the text with the configured emotes."""

    global config

    if not text:
        return None

    if config.emotes.list is None:
        return text

    for i in range(len(config.emotes.list)):
        word = config.emotes.list[str(i)]
        if word == "":
            continue
        tmp = re.compile(word, re.IGNORECASE)
        text = tmp.sub(osc.emote_keys[i], text)

    return text


def replace_words(text):
    """Replaces words in the text with the configured replacements."""

    global config

    if not text:
        return None

    text = text.strip()
    if not config.wordreplacement.enabled or config.wordreplacement.list == dict():
        return text

    for key, value in config.wordreplacement.list.items():
        tmp = re.compile(key, re.IGNORECASE)
        text = tmp.sub(value, text)

    text = re.sub(' +', ' ', text)
    return text


def set_typing_indicator(state: bool, textfield: bool = False):
    """Sets the typing indicator for the Chatbox and KAT."""

    global config
    global osc

    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.set_textbox_typing_indicator(state)
    if config.osc.use_kat and osc.isactive and not textfield:
        osc.set_kat_typing_indicator(state)
    if config.obs.enabled:
        browsersource.setFinished(state)


def clear_chatbox():
    """Clears the Chatbox, KAT and Overlay."""

    global config
    global osc
    global ovr
    global browsersource
    global transcriber

    if browsersource:
        browsersource.setText("")
    main_window.clear_textfield()
    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.clear_chatbox(config.mode == 0)
    if config.osc.use_kat and osc.isactive:
        osc.clear_kat()
    if ovr.initialized and config.overlay.enabled:
        ovr.set_overlay_text("")

    main_window.set_text_label("- No Text -")


def populate_chatbox(text, cutoff: bool = False, is_textfield: bool = False):
    """Populates the Chatbox, KAT and Overlay with the given text."""

    global config
    global main_window
    global osc
    global ovr
    global browsersource
    global timeout_time

    text = replace_words(text)

    if not text:
        return

    if browsersource:
        browsersource.setText(text)

    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.set_textbox_text(text, cutoff, config.mode == 0 and not is_textfield)

    if config.osc.use_kat and osc.isactive:
        _kat_text = text
        if config.emotes.enabled:
            _kat_text = replace_emotes(_kat_text)
        osc.set_kat_text(_kat_text, cutoff)

    if cutoff:
        text = text[-osc.textbox_charlimit:]
    else:
        text = text[:osc.textbox_charlimit]

    main_window.set_text_label(text)
    if ovr.initialized and config.overlay.enabled:
        ovr.set_overlay_text(text)

    set_typing_indicator(False)


def process_forever():
    """Processes audio data from the data queue until the user cancels the process by pressing the button again."""

    global config
    global main_window
    global pressed
    global config_ui_open
    global listen
    global transcriber
    global finished
    global timeout_time

    play_sound(config.audio_feedback.sound_listen)

    finished = False
    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")

    listen.start_listen_background()

    _time_last = time()
    while True:
        if config_ui_open:
            break

        if pressed:
            _time_last = time()
            _held = False
            while pressed:
                if time() - _time_last > config.listener.hold_time:
                    _held = True
                    break
                sleep(0.05)
            if _held:
                main_window.set_status_label("CLEARED", "#00008b")
                play_sound(config.audio_feedback.sound_clear)
                clear_chatbox()
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            pre = time()
            _np_audio = listen.raw_to_np(_last_sample)
            _text = transcriber.transcribe(_np_audio)
            if translator:
                main_window.set_status_label("TRANSLATING", "orange")
                play_sound(config.audio_feedback.sound_donelisten)
                _text = translator.translate(_text)
            main_window.set_time_label(time() - pre)

            _time_last = time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time() - _time_last > config.listener.pause_threshold:
            log.info(_text)
            set_typing_indicator(False)
            _last_sample = bytes()

        sleep(0.05)

    finished = True
    timeout_time = time()
    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()


def process_loop():
    """Processes audio data from the data queue and transcribes it until the user stops talking."""

    global config
    global listen
    global main_window
    global pressed
    global listen
    global transcriber
    global finished
    global timeout_time

    finished = False
    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound(config.audio_feedback.sound_listen)

    listen.start_listen_background()

    _time_last = time()
    while True:
        if pressed:
            _time_last = time()
            _held = False
            while pressed:
                if time() - _time_last > config.listener.hold_time:
                    _held = True
                    break
                sleep(0.05)
            if _held:
                main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
                play_sound(config.audio_feedback.sound_clear)
                clear_chatbox()
                break
            elif _last_sample == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                play_sound(config.audio_feedback.sound_timeout)
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            pre = time()
            _np_audio = listen.raw_to_np(_last_sample)
            _text = transcriber.transcribe(_np_audio)
            if translator:
                main_window.set_status_label("TRANSLATING", "orange")
                play_sound(config.audio_feedback.sound_donelisten)
                _text = translator.translate(_text)
            main_window.set_time_label(time() - pre)

            _time_last = time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time() - _time_last > config.listener.pause_threshold:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            log.info(_text)
            play_sound(config.audio_feedback.sound_finished)
            break
        elif _last_sample == bytes() and time() - _time_last > config.listener.timeout_time:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            play_sound(config.audio_feedback.sound_timeout)
            break
        sleep(0.05)

    finished = True
    timeout_time = time()
    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()


def process_once():
    """Process a single input and return the transcription."""

    global config
    global main_window
    global pressed
    global listen
    global finished
    global timeout_time

    finished = False
    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound(config.audio_feedback.sound_listen)
    raw_audio = listen.listen_once()
    if raw_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound(config.audio_feedback.sound_timeout)
        set_typing_indicator(False)
    else:
        play_sound(config.audio_feedback.sound_donelisten)
        set_typing_indicator(True)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            pre = time()
            _np_audio = listen.raw_to_np(raw_audio)
            _trans = transcriber.transcribe(_np_audio)
            if translator:
                play_sound(config.audio_feedback.sound_donelisten)
                main_window.set_status_label("TRANSLATING", "orange")
                _trans = translator.translate(_trans)
            main_window.set_time_label(time() - pre)
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound(config.audio_feedback.sound_timeout)
            elif _trans:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_trans)
                play_sound(config.audio_feedback.sound_finished)
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound(config.audio_feedback.sound_timeout)
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound(config.audio_feedback.sound_timeout)

    finished = True
    timeout_time = time()
    set_typing_indicator(False)
    main_window.set_button_enabled(True)


def get_trigger_state():
    """Returns the state of the trigger, either from the keyboard or the ovr action"""

    global config
    global ovr
    global initialized

    if not initialized:
        return False

    if ovr.initialized and ovr.get_ovraction_bstate():
        return True
    else:
        return is_pressed(config.hotkey)


def check_timeout():

    global timeout_time
    global finished

    if finished and config.text_timeout > 0 and timeout_time > 0 and time() - timeout_time > config.text_timeout:
        clear_chatbox()
        play_sound(config.audio_feedback.sound_timeout)
        finished = False
        timeout_time = 0.0


def handle_input():
    """Handles all input from the user"""

    global config
    global thread_process
    global held
    global holding
    global pressed
    global curr_time
    global config_ui_open
    global initialized

    if not initialized or config_ui_open:
        return

    pressed = get_trigger_state()
    check_timeout()

    if thread_process.is_alive():
        return

    if not thread_process.is_alive() and config.mode == 2 and not config_ui_open:
        thread_process = Thread(target=process_forever)
        thread_process.start()
    elif pressed and not holding and not held:
        holding = True
        curr_time = time()
    elif pressed and holding and not held:
        holding = True
        if time() - curr_time > config.listener.hold_time:
            clear_chatbox()
            main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
            play_sound(config.audio_feedback.sound_clear)
            held = True
            holding = False
    elif not pressed and holding and not held:
        held = True
        holding = False
        thread_process = Thread(target=process_loop if config.mode else process_once)
        thread_process.start()
    elif not pressed and held:
        held = False
        holding = False


def entrybox_enter_event(text):
    """Handles the enter event for the textfield."""

    global config
    global main_window
    global enter_pressed
    global finished
    global timeout_time
    global finished
    global timeout_time

    enter_pressed = True
    if text:
        if translator:
            play_sound(config.audio_feedback.sound_donelisten)
            text = translator.translate(text)
        populate_chatbox(text, False, True)
        play_sound(config.audio_feedback.sound_finished)
        main_window.clear_textfield()
    else:
        clear_chatbox()
        play_sound(config.audio_feedback.sound_clear)

    finished = True
    timeout_time = time()


def textfield_keyrelease(text):
    """Handles the key release event for the textfield."""

    global config
    global osc
    global enter_pressed
    global finished
    global timeout_time
    global finished
    global timeout_time

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
    finished = True
    timeout_time = time()


def main_window_closing():
    """Handles the closing of the main window."""

    global config
    global main_window
    global config_ui
    global osc
    global browsersource

    log.info("Closing...")
    try:
        osc.stop()
    except Exception:
        log.error(traceback.format_exc())
    try:
        main_window.on_closing()
    except Exception:
        log.error(traceback.format_exc())
    try:
        config_ui.on_closing()
    except Exception:
        log.error(traceback.format_exc())
    try:
        browsersource.stop()
    except Exception:
        log.error(traceback.format_exc())


def open_settings():
    """Opens the settings menu"""

    global config
    global main_window
    global config_ui
    global config_ui_open

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = SettingsWindow(config, CONFIG_PATH, __file__, main_window.get_coordinates)
    config_ui.button_refresh.configure(command=determine_energy_threshold)
    config_ui.btn_save.configure(command=(lambda: reload(True)))
    config_ui.tkui.protocol("WM_DELETE_WINDOW", reload)
    main_window.set_button_enabled(False)
    config_ui.open()


def determine_energy_threshold():
    """Determines the energy threshold for the microphone to use for speech recognition"""

    global config
    global config_ui
    global listen

    config_ui.set_energy_threshold("Be quiet for 5 seconds...")
    config_ui.set_energy_threshold(listen.get_energy_threshold())


def check_ovr():

    global config
    global initialized
    global ovr
    global config_ui_open
    global main_window

    if not initialized or config_ui_open or ovr.initialized or not OVRHandler.is_running():
        return

    log.info("SteamVR is running, reinitalizing...")
    ovr.init()
    main_window.set_conf_label(config.osc.ip, config.osc.client_port, config.osc.server_port, ovr.initialized, transcriber.device_name, transcriber.whisper_model, transcriber.compute_type, config.device.cpu_threads, config.device.num_workers)


def restart():
    """Restarts the program."""

    global main_window
    global config_ui

    
    executable = sys.executable
    log.info("Restarting...")
    try:
        coordinates = main_window.get_coordinates()
        tmp = sys.argv[0]
        sys.argv.clear()
        sys.argv.append(tmp)
        sys.argv.append(str(coordinates[0]))
        sys.argv.append(str(coordinates[1]))
        print(sys.argv)
    except Exception:
        log.error("Error restarting: ")
        log.error(traceback.format_exc())
    
    os.execl(executable, executable, *sys.argv)


def reload(save=False):
    """Handles the closing of the settings menu. If save is True, saves the settings and restarts the program."""

    global config
    global osc
    global config_ui
    global config_ui_open
    global browsersource

    if save and config_ui_open:
        try:
            config_ui.save()
            config_ui.on_closing()
        except Exception:
            log.error("Error saving settings: ")
            log.error(traceback.format_exc())
    elif config_ui_open:
        config_ui.on_closing()
        main_window.set_status_label("SETTINGS NOT SAVED - WAITING FOR INPUT", "#00008b")
    
    try:
        init()
    except Exception:
        log.error("Error reinitializing: ")
        log.error(traceback.format_exc())
        main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO cache/latest.log for more info on the error", "red")

    main_window.set_button_enabled(True)
    config_ui_open = False


if __name__ == "__main__":
    if os.name == 'nt':
        loadfont(get_absolute_path("resources/CascadiaCode.ttf", __file__))

    # Load config
    config = config_struct.load(CONFIG_PATH)

    if not is_available():
        config.whisper.device.type = "cpu"
        config.translator.device.type = "cpu"

    try:
        x = int(sys.argv[1])
        y = int(sys.argv[2])
    except Exception as e:
        x = None
        y = None

    main_window = MainWindow(__file__, x, y)

    main_window.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
    main_window.textfield.bind("<Return>", (lambda event: entrybox_enter_event(main_window.textfield.get())))
    main_window.textfield.bind("<KeyRelease>", (lambda event: textfield_keyrelease(main_window.textfield.get())))
    main_window.btn_settings.configure(command=open_settings)
    main_window.btn_refresh.configure(command=lambda: reload(True))
    main_window.create_loop(7000, check_ovr)
    main_window.create_loop(50, handle_input)
    main_window.tkui.after(100, reload)
    main_window.run_loop()
