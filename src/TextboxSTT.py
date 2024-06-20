try:
    import ctypes
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    DEBUG = len(sys.argv) <= 3

    from logger import LogToFile, get_absolute_path, force_single_instance
    if not DEBUG:
        force_single_instance()
    CACHE_PATH = get_absolute_path('../cache/', __file__)
    CONFIGS_PATH = get_absolute_path('../configs/', __file__)

    CURRENT_CONFIG = "default.json"
    DEFAULT_CONFIG = CONFIGS_PATH + CURRENT_CONFIG
    CURRENT_CONFIG_PATH = CONFIGS_PATH + "CURRENT_CONFIG"
    OUT_FILE_LOGGER = LogToFile(CACHE_PATH)
    sys.stdout = OUT_FILE_LOGGER
    sys.stderr = OUT_FILE_LOGGER

    import traceback
    from threading import Thread
    from time import time, sleep
    from keyboard import is_pressed, all_modifiers
    from ui import MainWindow, SettingsWindow, ChangeLogViewer
    from configurator import Configurator
    from osc import OscHandler
    from browsersource import BrowserHandler
    from ovr import OVRHandler
    from listen import ListenHandler
    from transcribe import TranscribeHandler
    from translate import TranslationHandler
    from websocket import WebsocketHandler
    from clipboard import clipboardHandler
    from config import config_struct, audio, LANGUAGE_TO_KEY
    from updater import Update_Handler
    from pydub import AudioSegment
    from helper import replace_words, replace_emotes, loadfont, measure_time
    from torch.cuda import is_available
    from autocorrect import Speller
    import winsound
    import copy
    import subprocess
    import logging
    import glob
    import re

    log = logging.getLogger("TextboxSTT")

    import pkg_resources
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    log.debug(installed_packages_list)
    log.debug("Python Version: " + sys.version)
    FIRST_LAUNCH = False
    VERSION = "DEV"
    try:
        VERSION = open(get_absolute_path("VERSION", __file__)).readline().rstrip()
    except Exception:
        log.error("Failed to read version file.")
    log.info(f"VRCTextboxSTT {VERSION} by I5UCC")

    python_version = sys.version.split(" ")[0].strip()
    if "3.12" not in python_version and "v2" in VERSION:
        ctypes.windll.user32.MessageBoxW(0, f"You are using an unsupported version of Python ({python_version}) for this version of TextboxSTT ({VERSION}), please reinstall the newest version of TextboxSTT from github.", "TextboxSTT - Unsupported Python Version", 0)

    try:
        os.mkdir(CONFIGS_PATH)
    except FileExistsError:
        pass
    except Exception:
        log.fatal("Failed to create cache directory: ")
        log.error(traceback.format_exc())
    
    # Move old config to new location
    old_config = get_absolute_path('../config.json', __file__)
    if os.path.isfile(old_config):
        if os.path.isfile(DEFAULT_CONFIG):
            os.remove(DEFAULT_CONFIG)
        log.info("Moving old config to new location...")
        os.rename(old_config, DEFAULT_CONFIG)
    
    if not os.path.isfile(CURRENT_CONFIG_PATH):
        with open(CONFIGS_PATH + "CURRENT_CONFIG", "w") as f:
            f.write("default.json")
    else:
        with open(CURRENT_CONFIG_PATH, "r") as f:
            CURRENT_CONFIG = f.readline().rstrip()

    if not os.path.isfile(DEFAULT_CONFIG):
        FIRST_LAUNCH = True
        config_struct.save(config_struct(), DEFAULT_CONFIG)

    CONFIG_PATH = CONFIGS_PATH + CURRENT_CONFIG
        
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
config_window: SettingsWindow = None
config: config_struct = None
updater: Update_Handler = None
osc: OscHandler = None
ovr: OVRHandler = None
listener: ListenHandler = None
transcriber: TranscribeHandler = None
translator: TranslationHandler = None
browsersource: BrowserHandler = None
websocket: WebsocketHandler = None
clipboard: clipboardHandler = None
autocorrect: Speller = None
timeout_time: float = 0.0
overlay_timeout_time: float = 0.0
curr_time: float = 0.0
pressed: bool = False
holding: bool = False
held: bool = False
thread_process: Thread = None
thread_pressed: Thread = None
initialized: bool = False
replacement_dict: dict = None
base_replacement_dict: dict = None


def init():
    """Initialize the application."""

    global config
    global main_window
    global osc
    global transcriber
    global translator
    global websocket
    global clipboard
    global ovr
    global initialized
    global browsersource
    global listener
    global autocorrect
    global updater
    global replacement_dict
    global base_replacement_dict

    initialized = False

    replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.list.items()}
    base_replacement_dict = {re.compile(key, re.IGNORECASE): value for key, value in config.wordreplacement.base_replacements.items()}
    modify_audio_files(config.audio_feedback.__dict__.copy())

    # Initialize Update Handler and Check for Updates
    if not updater:
        updater = Update_Handler(get_absolute_path("../git/bin/git.exe", __file__), os.path.abspath(sys.path[-1] + "\\..\\"), __file__)
        log.info(main_window.version)
        update_available, latest_tag = updater.check_for_updates(main_window.version)
        if update_available:
            main_window.show_update_button(f"Update Available! ({latest_tag})")
            main_window.btn_update.configure(command=update)

    # Initialize Clipboard Handler
    if not clipboard:
        clipboard = clipboardHandler()
        main_window.toggle_copy_button(not config.always_clipboard)
        main_window.btn_copy.configure(command=(lambda: clipboard.set_clipboard()))

    # Initialize Autocorrect
    if config.autocorrect.language and config.autocorrect.language in LANGUAGE_TO_KEY:
        autocorrect = Speller(LANGUAGE_TO_KEY[config.autocorrect.language])
    elif not config.autocorrect.language and autocorrect:
        del autocorrect

    # Initialize ListenHandler
    if not listener:
        listener = ListenHandler(config.listener)
    else:
        listener.set_config(config.listener)

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

    # Temporarily output to text label for download progress.
    OUT_FILE_LOGGER.set_ui_output(main_window.loading_status)
    main_window.set_status_label("LOADING WHISPER MODEL", "orange")
    # Initialize TranscribeHandler
    if not transcriber:
        transcriber = TranscribeHandler(copy.deepcopy(config.whisper), config.vad, CACHE_PATH, config.translator.language == "english")
        transcriber.transcribe()
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

    # Start Browser Handler
    if not browsersource:
        browsersource = BrowserHandler(config.obs, get_absolute_path('resources/obs_source.html', __file__), CACHE_PATH)
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

    main_window.set_text_label("- No Text -")
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")
    main_window.set_button_enabled(True)
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

    set_typing_indicator(False)

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
    global replacement_dict
    global base_replacement_dict
    global timeout_time
    global overlay_timeout_time
    global clipboard

    if config.wordreplacement.enabled:
        text = replace_words(text, replacement_dict)
        text = replace_words(text, base_replacement_dict)

    if not text:
        return

    clipboard.content = text

    if config.always_clipboard:
        clipboard.set_clipboard(text)

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
    timeout_time = time()
    overlay_timeout_time = time()

@measure_time
def transcribe_translate_populate(raw_audio: bytes, append: bool = False, last_text: str = "") -> tuple[str, float]:
    """
    Transcribes and translates the given raw audio, and populates the chatbox with the result.

    Args:
        raw_audio (bytes): The raw audio data to transcribe.
        append (bool, optional): Whether to append the transcribed text to the last text. Defaults to False.
        last_text (str, optional): The last text to append to. Defaults to "".

    Returns:
        tuple[str, float]: A tuple containing the transcribed/translated text and the time taken for the operation.
    """
    pre = time()
    set_typing_indicator(True)
    _np_audio = listener.raw_to_np(raw_audio)
    
    main_window.set_status_label("TRANSCRIBING", "orange")
    _text = transcriber.transcribe(_np_audio)
    if append:
        _text = last_text + _text
    if translator:
        main_window.set_status_label("TRANSLATING", "orange")
        play_sound(config.audio_feedback.sound_donelisten)
        _text = translator.translate(_text)

    if not _text:
        return ("", 0.0)
    
    populate_chatbox(_text, True)
    time_taken = time() - pre
    main_window.set_time_label(time_taken)
    return (_text, time_taken)


def should_start_new_phrase(text: str, _raw_audio: bytes, time_taken: float) -> bool:
    """
    Determines whether a new phrase should be started based on the given parameters.

    Args:
        text (str): The current text.
        _raw_audio (bytes): The raw audio data.
        time_taken (float): The time taken for transcription.

    Returns:
        bool: True if a new phrase should be started, False otherwise.
    """
    sentence_end = text and text[-1] in {".", "!", "?"}
    is_timeout = len(_raw_audio) > config.whisper.max_samples or time_taken > config.whisper.max_transciption_time
    if sentence_end and is_timeout:
        log.warning("Either max samples or max transcription time reached. Starting new phrase.")
        return True
    return False


def process_forever_once():
    """
    Listens consistently but only transcribes once instead of continuously.
    """
    
    global config
    global main_window
    global pressed
    global listener
    global transcriber

    play_sound(config.audio_feedback.sound_listen)

    _text = ""
    _raw_audio = bytes()

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    set_finished(False)
    main_window.set_status_label("LISTENING", "#FF00FF")

    listener.start_listen_background(True)

    _time_last = time()
    while True:
        if main_window.config_ui_open or config.mode != 3:
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
                break
        elif not listener.get_queue_empty():
            set_typing_indicator(True)
            set_finished(False)
            _raw_audio += listener.get_queue_data()
            _time_last = time()
        elif _raw_audio != bytes() and time() - _time_last > config.listener.pause_threshold:
            set_typing_indicator(False)
            set_finished(True)
            osc.textbox_sound_enabled = True
            play_sound(config.audio_feedback.sound_donelisten)
            _text, time_taken = transcribe_translate_populate(_raw_audio)
            log.info(f"Transcript: {_text}")
            _raw_audio = bytes()

        sleep(0.05)

    set_typing_indicator(False)
    set_finished(False)
    main_window.set_button_enabled(True)
    listener.stop_listen_background()


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
    global listener
    global transcriber

    play_sound(config.audio_feedback.sound_listen)

    _text = ""
    _raw_audio = bytes()
    last_text = ""
    append = False

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    set_finished(False)
    main_window.set_status_label("LISTENING", "#FF00FF")

    listener.start_listen_background()

    _time_last = time()
    while True:
        if main_window.config_ui_open or config.mode != 2:
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
                break
        elif not listener.get_queue_empty():
            set_typing_indicator(True)
            set_finished(False)
            _raw_audio += listener.get_queue_data()
            _text, time_taken = transcribe_translate_populate(_raw_audio, append, last_text)
            _time_last = time()

            if should_start_new_phrase(_text, _raw_audio, time_taken):
                last_text = _text + " "
                append = True
                _raw_audio = _raw_audio[-config.whisper.cutoff_buffer:]
            else:
                append = False
        elif _raw_audio != bytes() and time() - _time_last > config.listener.pause_threshold:
            set_typing_indicator(False)
            set_finished(True)
            osc.textbox_sound_enabled = True
            log.info(f"Transcript: {_text}")
            _raw_audio = bytes()
            append = False
            last_text = ""

        sleep(0.05)

    set_typing_indicator(False)
    set_finished(False)
    main_window.set_button_enabled(True)
    listener.stop_listen_background()


def process_loop() -> None:
    """
    Processes audio data from the data queue and transcribes it until the user stops talking.

    The function uses several global variables for configuration and state management.

    Returns:
        None
    """

    global config
    global listener
    global main_window
    global pressed
    global listener
    global transcriber

    finished = False
    _text = ""
    _time_last = None
    _raw_audio = bytes()
    last_text = ""
    append = False

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    set_finished(finished)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound(config.audio_feedback.sound_listen)

    listener.start_listen_background()

    osc.textbox_sound_enabled = True

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
            elif _raw_audio == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                play_sound(config.audio_feedback.sound_timeout)
                break
        elif not listener.data_queue.empty():
            set_typing_indicator(True)
            _raw_audio += listener.get_queue_data()
            _text, time_taken = transcribe_translate_populate(_raw_audio, append, last_text)
            _time_last = time()

            if should_start_new_phrase(_text, _raw_audio, time_taken):
                last_text = _text + " "
                append = True
                _raw_audio = _raw_audio[-config.whisper.cutoff_buffer:]
            else:
                append = False
        elif _raw_audio != bytes() and time() - _time_last > config.listener.pause_threshold:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            finished = True
            osc.textbox_sound_enabled = True
            play_sound(config.audio_feedback.sound_finished)
            break
        elif _raw_audio == bytes() and time() - _time_last > config.listener.timeout_time:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            play_sound(config.audio_feedback.sound_timeout)
            break
        sleep(0.05)

    if finished:
        log.info(f"Transcript: {_text}")
    set_typing_indicator(False)
    set_finished(finished)
    main_window.set_button_enabled(True)
    listener.stop_listen_background()


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
    global listener

    finished = False
    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    set_finished(finished)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound(config.audio_feedback.sound_listen)
    raw_audio = listener.listen_once()
    osc.textbox_sound_enabled = True

    if raw_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound(config.audio_feedback.sound_timeout)
    else:
        play_sound(config.audio_feedback.sound_donelisten)
        set_typing_indicator(True)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _text, _ = transcribe_translate_populate(raw_audio)
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound(config.audio_feedback.sound_timeout)
            elif _text:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_text)
                play_sound(config.audio_feedback.sound_finished)
                finished = True
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound(config.audio_feedback.sound_timeout)
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound(config.audio_feedback.sound_timeout)

    if finished:
        log.info(f"Transcript: {_text}")
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

    if config.overlay.timeout > 0 and overlay_timeout_time > 0 and time() - overlay_timeout_time > config.overlay.timeout:
        if ovr.initialized and config.overlay.enabled:
            ovr.set_overlay_text("")
            log.info("Overlay timeout")
        overlay_timeout_time = 0.0

    if config.text_timeout > 0 and timeout_time > 0 and time() - timeout_time > config.text_timeout:
        clear_chatbox()
        play_sound(config.audio_feedback.sound_timeout_text)
        timeout_time = 0.0


def handle_input() -> None:
    """
    Handles the input from the user and performs the necessary actions based on the input.
    """
    global config
    global held
    global holding
    global pressed
    global curr_time
    global main_window
    global initialized

    while True:
        if not initialized or main_window.config_ui_open:
            sleep(0.5)
            continue

        check_timeout()

        if config.mode == 2 and not main_window.config_ui_open:
            process_forever()
            continue
        elif config.mode == 3 and not main_window.config_ui_open:
            process_forever_once()
            continue
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
            if config.mode:
                process_loop()
            else:
                process_once()
            continue
        elif not pressed and held:
            held = False
            holding = False
        sleep(0.03)


def handle_trigger_state():
    """Checks if the trigger is pressed and sets the global variable pressed accordingly."""
    global pressed
    while True:
        pressed = get_trigger_state()
        sleep(0.03)


def entrybox_enter_event(text) -> None:
    """
    Process the enter key event for the entry box.

    Args:
        text (str): The text entered in the entry box.
    """

    global config
    global main_window

    main_window.enter_pressed = True
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
        osc.textbox_sound_enabled = True
        populate_chatbox(text, False, True)
        play_sound(config.audio_feedback.sound_finished)
        main_window.clear_textfield()
    else:
        clear_chatbox()
        play_sound(config.audio_feedback.sound_clear)


def entrybox_keyrelease(text, last_char) -> None:
    """
    Handles the key release event for the textfield.
    
    Args:
        text (str): The text in the textfield.
        last_char (str): The last character entered in the textfield.
    """

    global config
    global osc
    global autocorrect

    if autocorrect and last_char in {" ", ",", ".", "!", "?", ";", ":"}:
        corrected_text = autocorrect(text)
        if corrected_text != text:
            main_window.textfield.delete(0, len(text))
            main_window.textfield.insert(0, corrected_text)
            text = corrected_text

    if not main_window.enter_pressed:
        set_finished(False)
        if len(text) > osc.textbox_charlimit:
            main_window.textfield.delete(osc.textbox_charlimit, len(text))
            main_window.textfield.icursor(osc.textbox_charlimit)
        _is_text_empty = text == ""
        set_typing_indicator(not _is_text_empty, True)
        if _is_text_empty:
            clear_chatbox()
        else:
            osc.textbox_sound_enabled = False
            populate_chatbox(text, False, True)
    else:
        set_finished(True)

    main_window.enter_pressed = False


def main_window_closing() -> None:
    """Handles the closing of the main window."""

    global config
    global main_window
    global config_window
    global osc
    global browsersource
    global websocket

    x, y = main_window.get_coordinates()
    config.last_position_x = x
    config.last_position_y = y
    config_struct.save(config, CONFIG_PATH)

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
        config_window.on_closing()
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
    global config_window

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    main_window.config_ui_open = True
    config_window = SettingsWindow(config, CONFIG_PATH, __file__, main_window.get_coordinates, restart)
    config_window.button_refresh.configure(command=determine_energy_threshold)
    config_window.btn_save.configure(command=(lambda: reload(True)))
    config_window.button_reset_config.configure(command=open_configurator)
    config_window.button_force_update.configure(command=update)
    config_window.tkui.protocol("WM_DELETE_WINDOW", reload)
    main_window.set_button_enabled(False)
    config_window.open()

def open_configurator():
    global config_window

    if config_window:
        config_window.on_closing()
    Configurator(config, CONFIG_PATH, main_window.get_coordinates(), restart)

def determine_energy_threshold() -> None:
    """Determines the energy threshold for the microphone to use for speech recognition"""

    global config
    global config_window
    global listener

    config_window.set_energy_threshold("Be quiet for 5 seconds...")
    config_window.set_energy_threshold(listener.get_energy_threshold())


def check_ovr() -> None:
    """
    Checks the status of OpenVR and performs reinitialization if necessary.
    """
    global config
    global initialized
    global ovr
    global main_window

    if not initialized or main_window.config_ui_open or ovr.initialized or not OVRHandler.is_running():
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
    global config_window

    if main_window.config_ui_open:
        config_window.on_closing()

    def update_done():
        log.name = "TextboxSTT"
        restart()
    log.name = "Updater"

    coord = main_window.get_coordinates()

    cl_view = ChangeLogViewer(__file__, coord[0], coord[1])

    def update_now():
        try:
            main_window.btn_update
        except AttributeError:
            main_window.show_update_button("Updating...")

        main_window.btn_update.configure(text="Updating..." , state="disabled")
        main_window.update()
        cl_view.destroy()
        updater.update(update_done, main_window.set_text_label)

    def cancel_update():
        cl_view.destroy()
        main_window.btn_update.configure(state="normal")
        main_window.update()

    main_window.btn_update.configure(state="disabled")
    cl_view.run()
    cl_view.update()
    cl_view.button_install.configure(command=update_now)
    cl_view.button_close.configure(command=cancel_update)


def restart() -> None:
    """
    Restarts the program.
    """

    global main_window
    global config_window

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
    global config_window
    global main_window
    global browsersource

    if save and main_window.config_ui_open:
        try:
            config_window.save()
            config_window.on_closing()
        except Exception:
            log.error("Error saving settings: ")
            log.error(traceback.format_exc())
    elif main_window.config_ui_open:
        config_window.on_closing()
        main_window.set_status_label("SETTINGS NOT SAVED - WAITING FOR INPUT", "#00008b")
    
    try:
        init()
    except Exception:
        log.error("Error reinitializing: ")
        log.error(traceback.format_exc())
        main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO cache/latest.log for more info on the error", "red")

    main_window.set_button_enabled(True)
    main_window.config_ui_open = False


def load_fonts() -> None:
    """Loads all fonts in the resources/fonts folder on Windows."""

    font_path = get_absolute_path("resources/fonts/", __file__)
    if os.name == 'nt':
        fonts = glob.glob(font_path + "*.ttf")
        for font in fonts:
            log.info(f"Loading font: {font}")
            loadfont(font)


def change_profiles(*args):
    global config

    selected = main_window.dropdown_var.get() + ".json"
    log.info(f"Changing profile to {selected}")
    with open(CURRENT_CONFIG_PATH, "w") as f:
        f.write(selected)
    CONFIG_PATH = CONFIGS_PATH + selected
    config = config_struct.load(CONFIG_PATH)
    reload()


def add_profile(profile):
    if not profile:
        main_window.profile_toggle(False)
        return

    if not profile.endswith(".json"):
        profile += ".json"

    if os.path.isfile(CONFIGS_PATH + profile):
        main_window.profile_toggle(False)
        log.error(f"Profile {profile} already exists.")
    else:
        config_struct.save(config, CONFIGS_PATH + profile)

    main_window.dropdown_var.set(profile[:-5])
    main_window.refresh_profiles()
    change_profiles()
    main_window.profile_toggle(False)


def remove_profile(profile):
    if not profile or profile == "default.json":
        log.error("Cannot remove default profile.")
        return
    
    if os.path.isfile(CONFIGS_PATH + profile):
        os.remove(CONFIGS_PATH + profile)
    
    CURRENT_CONFIG = "default.json"

    with open(CURRENT_CONFIG_PATH, "w") as f:
        f.write(CURRENT_CONFIG)
    
    main_window.dropdown_var.set("default")
    main_window.refresh_profiles()
    change_profiles()


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
        x = config.last_position_x
        y = config.last_position_y

    main_window = MainWindow(__file__, CONFIGS_PATH, CURRENT_CONFIG, x, y, VERSION)
    main_window.dropdown_var.trace_add("write", change_profiles)

    main_window.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
    main_window.textfield.bind("<Return>", (lambda event: entrybox_enter_event(main_window.textfield.get())))
    main_window.textfield.bind("<KeyRelease>", (lambda event: entrybox_keyrelease(main_window.textfield.get(), event.char)))
    main_window.textfield_profile.bind("<Return>", (lambda event: add_profile(main_window.textfield_profile.get())))
    main_window.button_profile_remove.configure(command=(lambda: remove_profile(main_window.dropdown_var.get() + ".json")))
    main_window.btn_settings.configure(command=open_settings)
    main_window.btn_refresh.configure(command=restart)
    if FIRST_LAUNCH:
        open_configurator()

    main_window.create_loop(7000, check_ovr)
    main_window.tkui.update()
    thread_process = Thread(target=handle_input)
    thread_pressed = Thread(target=handle_trigger_state)
    thread_process.start()
    thread_pressed.start()
    main_window.tkui.after(0, reload)
    main_window.run_loop()
