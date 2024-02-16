try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    DEBUG = len(sys.argv) <= 3

    from logger import LogToFile, get_absolute_path, force_single_instance
    if DEBUG:
        CACHE_PATH = get_absolute_path('cache/', __file__)
        CONFIG_PATH = get_absolute_path('config.json', __file__)
    else:
        force_single_instance()
        CACHE_PATH = get_absolute_path('../cache/', __file__)
        CONFIG_PATH = get_absolute_path('../config.json', __file__)
    OUT_FILE_LOGGER = LogToFile(CACHE_PATH)
    sys.stdout = OUT_FILE_LOGGER
    sys.stderr = OUT_FILE_LOGGER

    import traceback
    from threading import Thread
    from time import time, sleep
    from keyboard import is_pressed, all_modifiers
    from ui import MainWindow, SettingsWindow
    from osc import OscHandler
    from browsersource import OBSBrowserSource
    from ovr import OVRHandler
    from listen import ListenHandler
    from transcribe import TranscribeHandler
    from translate import TranslationHandler
    from websocket import WebsocketHandler
    from config import config_struct, audio, LANGUAGE_TO_KEY
    from updater import Update_Handler
    from pydub import AudioSegment
    from helper import replace_words, replace_emotes, loadfont
    from torch.cuda import is_available
    from autocorrect import Speller
    import winsound
    import copy
    import subprocess
    import numpy as np
    import logging
    import pyperclip as clipboard
    import glob
    import re

    log = logging.getLogger("main")

    import pkg_resources
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    log.debug(installed_packages_list)
    log.debug("Python Version: " + sys.version)
    VERSION = "DEV"
    try:
        VERSION = open(get_absolute_path("VERSION", __file__)).readline().rstrip()
    except Exception:
        pass
    log.info(f"VRCTextboxSTT {VERSION} by I5UCC")
except FileNotFoundError as e:
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, f"Couldn't Import some dependencies, you might be missing C++ Redistributables needed for this program.\n\n Please try to reinstall the C++ Redistributables, link in the Requirements of the repository.\n\n{e}", "TextboxSTT - Dependency Error", 0)
    sys.exit(1)
except Exception as e:
    import ctypes
    import traceback
    ctypes.windll.user32.MessageBoxW(0, "Unexpected Error while importing dependencies.\n\n Please report the following Traceback to the repository or Discord.", "TextboxSTT - Unexpected Error", 0)
    ctypes.windll.user32.MessageBoxW(0, traceback.format_exc(), "TextboxSTT - Unexpected Error", 0)
    sys.exit(1)

main_window: MainWindow = None
config: config_struct = None
updater: Update_Handler = None
osc: OscHandler = None
ovr: OVRHandler = None
listen: ListenHandler = None
transcriber: TranscribeHandler = None
translator: TranslationHandler = None
browsersource: OBSBrowserSource = None
websocket: WebsocketHandler = None
autocorrect: Speller = None
timeout_time: float = 0.0
overlay_timeout_time: float = 0.0
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
curr_text: str = ""
replacement_dict: dict = {}
base_replacement_dict: dict = {}


def init():
    """Initialize the application."""

    global config
    global main_window
    global osc
    global transcriber
    global translator
    global websocket
    global ovr
    global initialized
    global browsersource
    global listen
    global autocorrect
    global updater
    global replacement_dict
    global base_replacement_dict

    replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.list.items()}
    base_replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.base_replacements.items()}

    main_window.toggle_copy_button(not config.always_clipboard)
    main_window.btn_copy.configure(command=(lambda: clipboard.copy(curr_text)))

    modify_audio_files(config.audio_feedback.__dict__.copy())

    if config.autocorrect.language and config.autocorrect.language in LANGUAGE_TO_KEY:
        autocorrect = Speller(LANGUAGE_TO_KEY[config.autocorrect.language])
    elif not config.autocorrect.language and autocorrect:
        del autocorrect

    # Initialize ListenHandler
    if not listen:
        listen = ListenHandler(config.listener)
    else:
        listen.set_config(config.listener)

    # Initialize OpenVR
    font_language = config.whisper.language if not config.translator.language else config.translator.language
    if not ovr:
        ovr = OVRHandler(config.overlay, __file__, font_language, DEBUG)
    if OVRHandler.is_running():
        ovr.init()
    if ovr.overlay_font != font_language:
        ovr.set_overlay_font(font_language)
    if ovr.initialized:
        log.info("Initialized OpenVR")
    else:
        log.warning("Failed to initialize OpenVR, continuing desktop only.")
    
    # Initialize OSC Handler
    if not osc:
        osc = OscHandler(config, copy.deepcopy(config.osc))
    elif osc.osc_ip != config.osc.ip or osc.osc_port != config.osc.client_port or osc.default_osc_server_port != config.osc.server_port:
        log.info("Changed OSC settings, restarting...")
        restart()
    else:
        osc.config_osc = copy.deepcopy(config.osc)
    log.info("Initialized OSC")

    # Start Flask server
    if not browsersource:
        browsersource = OBSBrowserSource(config.obs, get_absolute_path('resources/obs_source.html', __file__), CACHE_PATH)
    if config.obs.enabled and not browsersource.running:
        if browsersource.start():
            log.info("Initialized Flask Server")
        else:
            log.warning("Failed to initialize Flask Server, continuing without OBS Source")
    elif not config.obs.enabled and browsersource.running:
        log.warning("Changed OBS settings, restarting...")
        restart()

    # Initialize Websocket Handler
    if not websocket:
        websocket = WebsocketHandler(config.websocket.port, config.websocket.update_rate, config.websocket.is_client, config.websocket.uri)
    if config.websocket.enabled and not websocket.running:
        websocket.start()
        log.info("Initialized WebSocket Server")
    elif not config.websocket.enabled and websocket.running or config.websocket.is_client != websocket.is_client or config.websocket.uri != websocket.uri or config.websocket.port != websocket.port:
        log.warning("Changed WebSocket settings, restarting...")
        restart()
    if config.websocket.update_rate != websocket.update_rate:
        websocket.set_update_rate(config.websocket.update_rate)

    # Temporarily output to text label for download progress.
    OUT_FILE_LOGGER.set_ui_output(main_window.loading_status)
    main_window.set_status_label("LOADING WHISPER MODEL", "orange")
    if not transcriber:
        transcriber = TranscribeHandler(copy.deepcopy(config.whisper), config.vad, CACHE_PATH, config.translator.language == "english")
        log.info("Device: " + transcriber.device_name)
    elif config.whisper != transcriber.config_whisper:
        log.warning("Changed Whisper settings, restarting...")
        restart()
    else:
        transcriber.config_whisper = copy.deepcopy(config.whisper)
    main_window.set_status_label(f"LOADED \"{transcriber.whisper_model}\"", "orange")

    # Initialize TranslationHandler
    if config.translator.language and config.translator.language != config.whisper.language and transcriber.task == "transcribe":
        main_window.set_status_label("LOADING TRANSLATION MODEL", "orange")
        if not translator:
            translator = TranslationHandler(CACHE_PATH, config.whisper.language, copy.deepcopy(config.translator))
        elif config.translator != translator.translator_config:
            log.warning("Changed Translator settings, restarting...")
            restart()
    elif translator:
        log.warning("Changed Translator settings, restarting...")
        restart()
    OUT_FILE_LOGGER.remove_ui_output()
    
    main_window.set_text_label("- No Text -")
    main_window.set_conf_label(config.osc.ip, config.osc.client_port, osc.osc_server_port, osc.http_port, ovr.initialized, transcriber.device_name, transcriber.whisper_model, transcriber.compute_type, config.whisper.device.cpu_threads, config.whisper.device.num_workers, config.vad.enabled)
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")
    main_window.set_button_enabled(True)

    if not updater:
        updater = Update_Handler(get_absolute_path("../git/bin/git.exe", __file__), os.path.abspath(sys.path[-1] + "\\..\\"), __file__)
        log.info(main_window.version)
        update_available, latest_tag = updater.check_for_updates(main_window.version)
        if update_available:
            main_window.show_update_button(f"Update Available! ({latest_tag})")
            main_window.btn_update.configure(command=update)

    initialized = True


def modify_audio_files(audio_dict):
    """
    Modifies audio files in the given audio_dict.

    Parameters:
        audio_dict (dict): A dictionary containing information about audio files.

    Returns:
        None
    """
    del audio_dict["enabled"]
    for key in audio_dict:
        try:
            _tmp_audio: audio = audio_dict[key]
            _segment = AudioSegment.from_wav(get_absolute_path(f"resources/{_tmp_audio.file}", __file__))
            _segment = _segment + _tmp_audio.gain
            _segment.export(get_absolute_path(f"{CACHE_PATH}{_tmp_audio.file}", __file__), format="wav")
        except Exception:
            log.error(f"Failed to modify audio file \"{_tmp_audio.file}\": ")
            log.error(traceback.format_exc())


def play_sound(au: audio) -> None:
    """
    Play a sound file.

    Args:
        au (audio): The audio object containing the file to be played.

    Returns:
        None
    """
    global config

    if not config.audio_feedback.enabled:
        return

    _file = get_absolute_path(f"{CACHE_PATH}{au.file}", __file__)
    if not os.path.isfile(_file):
        log.info(f"Sound file \"{_file}\" does not exist.")
        return

    try:
        winsound.PlaySound(_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        log.error(f"Failed to play sound \"{_file}\": ")
        log.error(traceback.format_exc())


def set_typing_indicator(state: bool, textfield: bool = False) -> None:
    """
    Sets the typing indicator state for the textbox and/or KAT.

    Args:
        state (bool): The state of the typing indicator (True for active, False for inactive).
        textfield (bool, optional): Indicates whether the typing indicator should be set for the textbox. 
            Defaults to False.

    Returns:
        None
    """

    global config
    global osc

    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.set_textbox_typing_indicator(state)
    if config.osc.use_kat and osc.isactive and not textfield:
        osc.set_kat_typing_indicator(state)


def set_finished(state: bool) -> None:
    """
    Sets the finished state for browsersource and/or websocket.
    Determines whether the transcription is finished.

    Args:
        state (bool): The finished state to set.

    Returns:
        None
    """
    if config.obs.enabled:
        browsersource.setFinished(state)
    if config.websocket.enabled:
        websocket.set_finished(state)


def clear_chatbox() -> None:
    """
    Clears text in all output sources.
    """
    global config
    global osc
    global ovr
    global browsersource
    global websocket
    global transcriber
    global finished
    global timeout_time
    global overlay_timeout_time

    if browsersource:
        browsersource.setText("")
    if websocket:
        websocket.set_text("")
    main_window.clear_textfield()
    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.clear_chatbox(config.mode == 0)
    if config.osc.use_kat and osc.isactive:
        osc.clear_kat()
    if ovr.initialized and config.overlay.enabled:
        ovr.set_overlay_text("")

    finished = False
    overlay_timeout_time = 0.0
    timeout_time = 0.0

    main_window.set_text_label("- No Text -")


def populate_chatbox(text, cutoff: bool = False, is_textfield: bool = False):
    """
    Populates all output sources with the given text.

    Args:
        text (str): The text to populate the chatbox with.
        cutoff (bool, optional): Whether to truncate the text if it exceeds the character limit. Defaults to False.
        is_textfield (bool, optional): Whether the text is from a text field. Defaults to False.
    """

    global config
    global main_window
    global osc
    global ovr
    global browsersource
    global websocket
    global curr_text
    global replacement_dict
    global base_replacement_dict

    if config.wordreplacement.enabled:
        text = replace_words(text, replacement_dict)
        text = replace_words(text, base_replacement_dict)

    if not text:
        return

    curr_text = text

    if config.always_clipboard:
        clipboard.copy(text)

    if browsersource:
        browsersource.setText(text)

    if websocket:
        websocket.set_text(text)

    if config.osc.use_textbox and config.osc.use_both or config.osc.use_textbox and config.osc.use_kat and not osc.isactive or not config.osc.use_kat:
        osc.set_textbox_text(text, cutoff, config.mode == 0 and not is_textfield)

    if config.osc.use_kat and osc.isactive:
        _kat_text = text
        if config.emotes.enabled:
            _kat_text = replace_emotes(_kat_text, config.emotes.list, osc.emote_keys)
        osc.set_kat_text(_kat_text, cutoff)

    if cutoff:
        text = text[-osc.textbox_charlimit:]
    else:
        text = text[:osc.textbox_charlimit]

    main_window.set_text_label(text)
    if ovr.initialized and config.overlay.enabled:
        ovr.set_overlay_text(text)

    set_typing_indicator(False)


def process_forever() -> None:
    """
    Processes audio data from the data queue until the user cancels the process.

    The function uses several global variables for configuration and state management.

    Returns:
        None
    """

    global config
    global main_window
    global pressed
    global config_ui_open
    global listen
    global transcriber
    global finished
    global timeout_time
    global overlay_timeout_time

    play_sound(config.audio_feedback.sound_listen)

    finished = False
    _text = ""
    _time_last = None
    _last_sample = bytes()
    last_text = ""
    append = False
    first_run = True

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    set_finished(finished)
    main_window.set_status_label("LISTENING", "#FF00FF")

    listen.start_listen_background()

    _time_last = time()
    while True:
        if config_ui_open or config.mode != 2:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
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
                finished = False
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            pre = time()
            _np_audio = listen.raw_to_np(_last_sample)
            _text = transcriber.transcribe(_np_audio)
            log.info("Transcription: " + _text)
            
            if append:
                _text = last_text + _text
            if translator:
                main_window.set_status_label("TRANSLATING", "orange")
                play_sound(config.audio_feedback.sound_donelisten)
                _text = translator.translate(_text)
            time_taken = time() - pre
            main_window.set_time_label(time_taken)
            log.debug(f"Time taken: {time_taken}")

            _time_last = time()
            if not _text:
                continue
            populate_chatbox(_text, True)

            sentence_end = _text and _text[-1] in {".", "!", "?"}
            if sentence_end and not first_run and (len(_last_sample) > config.whisper.max_samples or time_taken > config.whisper.max_transciption_time):
                log.warning("Either max samples or max transcription time reached. Starting new phrase.")
                last_text = _text + " "
                append = True
                _last_sample = _last_sample[-config.whisper.cutoff_buffer:]
            
            first_run = False
        elif _last_sample != bytes() and time() - _time_last > config.listener.pause_threshold:
            set_typing_indicator(False)
            finished = True
            set_finished(finished)
            _last_sample = bytes()
            append = False

        sleep(0.05)

    timeout_time = time()
    overlay_timeout_time = time()
    set_typing_indicator(False)
    set_finished(False)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()


def process_loop() -> None:
    """
    Processes audio data from the data queue and transcribes it until the user stops talking.

    The function uses several global variables for configuration and state management.

    Returns:
        None
    """

    global config
    global listen
    global main_window
    global pressed
    global listen
    global transcriber
    global finished
    global timeout_time
    global overlay_timeout_time

    finished = False
    _text = ""
    _time_last = None
    _last_sample = bytes()
    last_text = ""
    append = False
    first_run = True

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    set_finished(finished)
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
                finished = False
                break
            elif _last_sample == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                play_sound(config.audio_feedback.sound_timeout)
                finished = False
                break
        elif not listen.data_queue.empty():
            while not listen.data_queue.empty():
                data = listen.data_queue.get()
                _last_sample += data

            pre = time()
            _np_audio = listen.raw_to_np(_last_sample)
            _text = transcriber.transcribe(_np_audio)
            log.info("Transcription: " + _text)
            if append:
                _text = last_text + _text
            if translator:
                main_window.set_status_label("TRANSLATING", "orange")
                play_sound(config.audio_feedback.sound_donelisten)
                _text = translator.translate(_text)
            time_taken = time() - pre
            main_window.set_time_label(time_taken)
            log.debug(f"Time taken: {time_taken}")

            _time_last = time()
            if not _text:
                continue
            populate_chatbox(_text, True)

            sentence_end = _text and _text[-1] in {".", "!", "?"}
            if sentence_end and not first_run and (len(_last_sample) > config.whisper.max_samples or time_taken > config.whisper.max_transciption_time):
                log.warning("Either max samples or max transcription time reached. Starting new phrase.")
                last_text = _text + " "
                append = True
                _last_sample = _last_sample[-config.whisper.cutoff_buffer:]
            
            first_run = False
        elif _last_sample != bytes() and time() - _time_last > config.listener.pause_threshold:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            finished = True
            play_sound(config.audio_feedback.sound_finished)
            break
        elif _last_sample == bytes() and time() - _time_last > config.listener.timeout_time:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            play_sound(config.audio_feedback.sound_timeout)
            finished = False
            break
        sleep(0.05)

    timeout_time = time()
    overlay_timeout_time = time()
    set_typing_indicator(False)
    set_finished(finished)
    main_window.set_button_enabled(True)
    listen.stop_listen_background()


def process_once():
    """
    Process audio input once.

    This function listens for audio input, transcribes it, and performs additional processing such as translation.
    It updates the status labels and plays audio feedback based on the processing results.

    Returns:
        None
    """
    global config
    global main_window
    global pressed
    global listen
    global finished
    global timeout_time
    global overlay_timeout_time

    finished = False
    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    set_finished(finished)
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
            _text = transcriber.transcribe(_np_audio)
            log.info("Transcription: " + _text)
            if translator:
                play_sound(config.audio_feedback.sound_donelisten)
                main_window.set_status_label("TRANSLATING", "orange")
                _text = translator.translate(_text)
            time_taken = time() - pre
            main_window.set_time_label(time_taken)
            log.debug(f"Time taken: {time_taken}")
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound(config.audio_feedback.sound_timeout)
                finished = False
            elif _text:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_text)
                play_sound(config.audio_feedback.sound_finished)
                finished = True
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound(config.audio_feedback.sound_timeout)
                finished = False
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound(config.audio_feedback.sound_timeout)
            finished = False

    timeout_time = time()
    overlay_timeout_time = time()
    set_typing_indicator(False)
    set_finished(finished)
    main_window.set_button_enabled(True)


def get_trigger_state() -> bool:
    """
    Returns the trigger state based on the configured hotkey and OpenVR action.

    Returns:
        bool: True if the trigger is activated, False otherwise.
    """
    global config
    global ovr
    global initialized

    if not initialized:
        return False

    if ovr.initialized and ovr.get_ovraction_bstate():
        return True

    hotkey_pressed = is_pressed(config.hotkey)
    if hotkey_pressed and "+" not in config.hotkey:
        modifier_pressed = False
        for modifier in all_modifiers:
            try:
                if is_pressed(modifier):
                    modifier_pressed = True
                    break
            except ValueError:
                pass
        return is_pressed(config.hotkey) and not modifier_pressed
    else:
        return hotkey_pressed


def check_timeout() -> None:
    """
    Checks if the timeout conditions are met and performs the necessary actions.

    This function checks if the speech-to-text process has finished and if the timeout
    conditions for the overlay and text are met. If the conditions are met, it clears
    the chatbox, plays a sound, and resets the necessary variables.
    """
    global timeout_time
    global overlay_timeout_time
    global finished

    if finished and config.overlay.timeout > 0 and overlay_timeout_time > 0 and time() - overlay_timeout_time > config.overlay.timeout:
        if ovr.initialized and config.overlay.enabled:
            ovr.set_overlay_text("")
        overlay_timeout_time = 0.0

    if finished and config.text_timeout > 0 and timeout_time > 0 and time() - timeout_time > config.text_timeout:
        clear_chatbox()
        play_sound(config.audio_feedback.sound_timeout_text)
        finished = False
        timeout_time = 0.0


def handle_input() -> None:
    """
    Handles the input from the user and performs the necessary actions based on the input.
    """
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


def entrybox_enter_event(text) -> None:
    """
    Process the entered text in the entry box.

    Args:
        text (str): The text entered in the entry box.
    """

    global config
    global main_window
    global enter_pressed
    global finished
    global timeout_time
    global overlay_timeout_time

    enter_pressed = True
    if text:
        if autocorrect:
            corrected_text = autocorrect(text)
            if corrected_text != text:
                main_window.textfield.delete(0, len(text))
                main_window.textfield.insert(0, corrected_text)
                text = corrected_text

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
    overlay_timeout_time = time()


def textfield_keyrelease(text, last_char) -> None:
    """
    Handles the key release event for the textfield.
    
    Args:
        text (str): The text in the textfield.
        last_char (str): The last character entered in the textfield.
    """

    global config
    global osc
    global enter_pressed
    global finished
    global timeout_time
    global overlay_timeout_time
    global autocorrect

    if autocorrect and last_char in {" ", ",", ".", "!", "?", ";", ":"}:
        corrected_text = autocorrect(text)
        if corrected_text != text:
            main_window.textfield.delete(0, len(text))
            main_window.textfield.insert(0, corrected_text)
            text = corrected_text

    if not enter_pressed:
        set_finished(False)
        if len(text) > osc.textbox_charlimit:
            main_window.textfield.delete(osc.textbox_charlimit, len(text))
            main_window.textfield.icursor(osc.textbox_charlimit)
        _is_text_empty = text == ""
        set_typing_indicator(not _is_text_empty, True)
        if _is_text_empty:
            clear_chatbox()
        else:
            populate_chatbox(text, False, True)
    else:
        set_finished(True)

    enter_pressed = False
    finished = True
    timeout_time = time()
    overlay_timeout_time = time()


def main_window_closing() -> None:
    """Handles the closing of the main window."""

    global config
    global main_window
    global config_ui
    global osc
    global browsersource
    global websocket

    log.info("Closing...")
    try:
        osc.stop()
    except Exception:
        pass
    try:
        main_window.on_closing()
    except Exception:
        pass
    try:
        config_ui.on_closing()
    except Exception:
        pass
    try:
        browsersource.stop()
    except Exception:
        pass
    try:
        websocket.stop()
    except Exception:
        pass
    os._exit(0)


def open_settings() -> None:
    """Opens the settings menu"""

    global config
    global main_window
    global config_ui
    global config_ui_open

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = SettingsWindow(config, CONFIG_PATH, __file__, main_window.get_coordinates, restart)
    config_ui.button_refresh.configure(command=determine_energy_threshold)
    config_ui.btn_save.configure(command=(lambda: reload(True)))
    config_ui.button_force_update.configure(command=update)
    config_ui.tkui.protocol("WM_DELETE_WINDOW", reload)
    main_window.set_button_enabled(False)
    config_ui.open()


def determine_energy_threshold() -> None:
    """Determines the energy threshold for the microphone to use for speech recognition"""

    global config
    global config_ui
    global listen

    config_ui.set_energy_threshold("Be quiet for 5 seconds...")
    config_ui.set_energy_threshold(listen.get_energy_threshold())


def check_ovr() -> None:
    """
    Checks the status of the Oculus Virtual Reality (OVR) system and performs reinitialization if necessary.

    This function checks if the OVR system is already initialized and if the configuration UI is open. If any of these conditions are met, the function returns without performing any action. Otherwise, it checks if SteamVR is running and if the OVRHandler is currently running. If both conditions are met, the function reinitalizes the OVR system.

    Note:
    - The global variables `config`, `initialized`, `ovr`, `config_ui_open`, and `main_window` are assumed to be defined and accessible within the scope of this function.

    Returns:
    None
    """
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


def update() -> None:
    """
    Function to update the application.
    """
    global updater
    global main_window
    global config_ui_open
    global config_ui

    if config_ui_open:
        config_ui.on_closing()

    def update_done():
        log.name = "TextboxSTT"
        restart()
    log.name = "Updater"

    try:
        main_window.btn_update
    except AttributeError:
        main_window.show_update_button("Updating...")

    main_window.btn_update.configure(text="Updating..." , state="disabled")
    updater.update(update_done, main_window.set_text_label)


def restart() -> None:
    """
    Restarts the program.
    """

    global main_window
    global config_ui

    executable = sys.executable
    log.info("Restarting...")
    try:
        coordinates = main_window.get_coordinates()
        tmp = copy.deepcopy(sys.argv)
        sys.argv.clear()
        sys.argv.append(tmp[0])
        sys.argv.append(str(coordinates[0]))
        sys.argv.append(str(coordinates[1]))
        sys.argv.append(tmp[3])
    except Exception:
        log.error("Error restarting: ")
        log.error(traceback.format_exc())

    log.info("Restarting with: " + executable + " " + " ".join(sys.argv))

    subprocess.Popen([executable, *sys.argv])
    main_window_closing()


def reload(save=False) -> None:
    """
    Handles the closing of the settings menu. If save is True, saves the settings and restarts the program.
    """

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


def load_fonts() -> None:
    """Loads all fonts in the resources/fonts folder on Windows."""

    font_path = get_absolute_path("resources/fonts/", __file__)
    if os.name == 'nt':
        fonts = glob.glob(font_path + "*.ttf")
        for font in fonts:
            log.info(f"Loading font: {font}")
            loadfont(font)


if __name__ == "__main__":
    # Load config
    config = config_struct.load(CONFIG_PATH)

    load_fonts()

    if not is_available():
        config.whisper.device.type = "cpu"
        config.translator.device.type = "cpu"

    try:
        x = int(sys.argv[1])
        y = int(sys.argv[2])
    except Exception as e:
        x = None
        y = None

    main_window = MainWindow(__file__, x, y, VERSION)

    main_window.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
    main_window.textfield.bind("<Return>", (lambda event: entrybox_enter_event(main_window.textfield.get())))
    main_window.textfield.bind("<KeyRelease>", (lambda event: textfield_keyrelease(main_window.textfield.get(), event.char)))
    main_window.btn_settings.configure(command=open_settings)
    main_window.btn_refresh.configure(command=restart)
    main_window.create_loop(7000, check_ovr)
    main_window.create_loop(50, handle_input)
    main_window.tkui.after(100, reload)
    main_window.run_loop()
