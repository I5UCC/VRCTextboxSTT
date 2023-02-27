import os
import sys
import json
import logging
from helper import LogToFile, loadfont, get_absolute_path, play_sound


VERSION = "v0.7"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
LOGFILE = get_absolute_path('out.log', __file__)
CONFIG_PATH = get_absolute_path('config.json', __file__)
CONFIG = json.load(open(CONFIG_PATH))


open(LOGFILE, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = LogToFile(log, logging.INFO, LOGFILE)
sys.stderr = LogToFile(log, logging.ERROR, LOGFILE)


if os.name == 'nt':
    loadfont(get_absolute_path("resources/CascadiaCode.ttf", __file__))


import threading
import time
import keyboard
import numpy as np
import speech_recognition as sr
import openvr
import whisper
import torch
import re
from osc import OscHandler
from ui import MainWindow, SettingsWindow
from queue import Queue
from PIL import Image, ImageDraw, ImageFont
import ctypes
import textwrap


osc: OscHandler = None
use_kat: bool = True
use_textbox: bool = True
use_both: bool = True
model: whisper = None
language: str = ""
task: str = "transcribe"
use_cpu: bool = False
rec: sr.Recognizer = None
source: sr.Microphone = None
data_queue: Queue = Queue()
ovr_initialized: bool = False
application: openvr.IVRSystem = None
action_set_handle: int = None
button_action_handle: int = None
overlay_handle: int = None
overlay_font: ImageFont.FreeTypeFont = None
curr_time: float = 0.0
pressed: bool = False
holding: bool = False
held: bool = False
thread_process: threading.Thread = threading.Thread()
config_ui: SettingsWindow = None
config_ui_open: bool = False
enter_pressed: bool = False


def init():
    global main_window
    global osc
    global use_textbox
    global use_kat
    global use_both
    global model
    global language
    global task
    global use_cpu
    global rec
    global source
    global data_queue
    global ovr_initialized
    global application
    global action_set_handle
    global button_action_handle
    global overlay_handle
    global overlay_font

    osc = OscHandler(CONFIG["osc_ip"], CONFIG["osc_port"], CONFIG["osc_ip"], CONFIG["osc_server_port"])
    use_textbox = bool(CONFIG["use_textbox"])
    use_kat = bool(CONFIG["use_kat"])
    use_both = bool(CONFIG["use_both"])

    _whisper_model = CONFIG["model"].lower()
    language = CONFIG["language"].lower()
    if language == "":
        language = None
    elif _whisper_model != "large" and language == "english" and ".en" not in _whisper_model:
        _whisper_model = _whisper_model + ".en"
    task = "translate" if CONFIG["translate_to_english"] and language != "english" else "transcribe"
    print(f"Using model: {_whisper_model} for language: {language} ({task}) ")

    # Temporarily output stderr to text label for download progress.
    if not os.path.isfile(get_absolute_path(f"whisper_cache/{_whisper_model}.pt", __file__)):
        sys.stderr.write = main_window.loading_status
    else:
        print("Whisper model already in cache.")

    main_window.set_status_label(f"LOADING \"{_whisper_model}\" MODEL", "orange")
    # Load Whisper model
    device = "cpu" if bool(CONFIG["use_cpu"]) or not torch.cuda.is_available() else "cuda"
    model = whisper.load_model(_whisper_model, download_root=get_absolute_path("whisper_cache/", __file__), in_memory=True, device=device)
    sys.stderr = LogToFile(log, logging.ERROR, LOGFILE)
    use_cpu = True if str(model.device) == "cpu" else False

    main_window.set_status_label(f"TESTING CONFIGURATION", "orange")
    model.transcribe(torch.zeros(256), fp16=not use_cpu, language=language, without_timestamps=True)

    # load the speech recognizer and set the initial energy threshold and pause threshold
    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = bool(CONFIG["dynamic_energy_threshold"])
    rec.energy_threshold = int(CONFIG["energy_threshold"])
    rec.pause_threshold = float(CONFIG["pause_threshold"])

    source = sr.Microphone(sample_rate=16000, device_index=int(CONFIG["microphone_index"]) if CONFIG["microphone_index"] else None)
    data_queue = Queue()

    # Initialize OpenVR
    main_window.set_status_label("INITIALIZING OVR", "orange")
    ovr_initialized = False
    try:
        application = openvr.init(openvr.VRApplication_Scene)
        overlay_handle = openvr.VROverlay().createOverlay("TextboxSTT", "TextboxSTT Transcription Overlay")
        openvr.VROverlay().setOverlayWidthInMeters(overlay_handle, 1)
        openvr.VROverlay().setOverlayColor(overlay_handle, 1.0, 1.0, 1.0)
        openvr.VROverlay().setOverlayAlpha(overlay_handle, 1)
        overlay_font = ImageFont.truetype(get_absolute_path("resources/CascadiaCode.ttf"), 46)
        set_overlay_position_hmd()
        action_path = get_absolute_path("bindings/textboxstt_actions.json", __file__)
        appmanifest_path = get_absolute_path("app.vrmanifest", __file__)
        openvr.VRApplications().addApplicationManifest(appmanifest_path)
        openvr.VRInput().setActionManifestPath(action_path)
        action_set_handle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
        button_action_handle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
        ovr_initialized = True
        main_window.set_status_label("INITIALZIED OVR", "green")
    except Exception:
        ovr_initialized = False
        main_window.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "red")

    main_window.set_conf_label(CONFIG["osc_ip"], CONFIG["osc_port"], CONFIG["osc_server_port"], ovr_initialized, use_cpu, _whisper_model)
    main_window.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")


def set_overlay_text(text: str):
    global overlay_handle
    global overlay_font

    if text == "":
        openvr.VROverlay().hideOverlay(overlay_handle)
        return

    openvr.VROverlay().showOverlay(overlay_handle)
    text = textwrap.fill(text, 70)

    _width = 1920
    _height = 200

    _img = Image.new("RGBA", (_width, _height))
    _draw = ImageDraw.Draw(_img)
    _draw.text((_width/2, _height/2), text, font=overlay_font, fill="white", anchor="mm", stroke_width=2, stroke_fill="black", align="center")
    _img_data = _img.tobytes()

    _buffer = (ctypes.c_char * len(_img_data)).from_buffer_copy(_img_data)

    openvr.VROverlay().setOverlayRaw(overlay_handle, _buffer, _width, _height, 4)


def set_overlay_position_hmd(x = 0, y = -0.4, size = 1, distance = -1):
    global overlay_handle

    overlay_matrix = openvr.HmdMatrix34_t()
    overlay_matrix[0][0] = size
    overlay_matrix[1][1] = size
    overlay_matrix[2][2] = size
    overlay_matrix[0][3] = x
    overlay_matrix[1][3] = y
    overlay_matrix[2][3] = distance

    openvr.VROverlay().setOverlayTransformTrackedDeviceRelative(overlay_handle, openvr.k_unTrackedDeviceIndex_Hmd, overlay_matrix)


def replace_emotes(text):
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
    if not text:
        return None

    text = text.strip()
    if CONFIG["word_replacements"] == {}:
        return text

    for key, value in CONFIG["word_replacements"].items():
        tmp = re.compile(key, re.IGNORECASE)
        text = tmp.sub(value, text)

    text = re.sub(' +', ' ', text)
    return text


def set_typing_indicator(state: bool, textfield: bool = False):
    global use_textbox
    global use_kat
    global use_both
    global osc

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.set_textbox_typing_indicator(state)
    if use_kat and osc.isactive and not textfield:
        osc.set_kat_typing_indicator(state)


def clear_chatbox():
    global use_textbox
    global use_kat
    global use_both
    global osc

    main_window.clear_textfield()
    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.clear_chatbox(CONFIG["mode"] == 0)
    if use_kat and osc.isactive:
        osc.clear_kat()
    main_window.set_text_label("- No Text -")
    set_overlay_text("")


def populate_chatbox(text, cutoff: bool = False, is_textfield: bool = False):
    global main_window
    global use_textbox
    global use_kat
    global use_both
    global osc

    text = replace_words(text)

    if not text:
        return

    if use_textbox and use_both or use_textbox and use_kat and not osc.isactive or not use_kat:
        osc.set_textbox_text(text, cutoff, CONFIG["mode"] == 0 and not is_textfield)

    if use_kat and osc.isactive:
        if CONFIG["enable_emotes"]:
            text = replace_emotes(text)
        osc.set_kat_text(text, cutoff)

    if cutoff:
        text = text[-osc.textbox_charlimit:]
    else:
        text = text[:osc.textbox_charlimit]
    
    main_window.set_text_label(text)
    set_overlay_text(text)

    set_typing_indicator(False)


def listen_once():
    global rec

    with source:
        try:
            _audio = rec.listen(source, timeout=float(CONFIG["timeout_time"]))
        except sr.WaitTimeoutError:
            return None

        return torch.from_numpy(np.frombuffer(_audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def transcribe(torch_audio, last_tokens = []):
    global use_cpu
    global language
    global model
    global task

    _options = {"without_timestamps": True, "prompt": last_tokens, "task": task}
    _result = model.transcribe(torch_audio, fp16=not use_cpu, language=language, **_options)

    _text = _result['text']
    _tokens = []
    for segment in _result['segments']:
        _tokens += segment['tokens']
        
    return (_text, _tokens)


def process_forever():
    global data_queue
    global source
    global rec
    global main_window
    global pressed
    global config_ui_open

    play_sound("listen", __file__)

    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(True)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")

    def record_callback(_, audio:sr.AudioData) -> None:
        _data = audio.get_raw_data()
        data_queue.put(_data)

    _stop_listening = rec.listen_in_background(source, record_callback, phrase_time_limit=CONFIG["phrase_time_limit"])

    _time_last = time.time()
    _last_tokens = []
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
                play_sound("clear", __file__)
                clear_chatbox()
                break
        elif not data_queue.empty():
            while not data_queue.empty():
                data = data_queue.get()
                _last_sample += data

            _torch_audio = torch.from_numpy(np.frombuffer(_last_sample, np.int16).flatten().astype(np.float32) / 32768.0)

            _transcription = transcribe(_torch_audio, _last_tokens)
            _text = _transcription[0]
            _last_tokens = _transcription[1]
                
            _time_last = time.time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time.time() - _time_last > CONFIG["pause_threshold"]:
            print(_text)
            _last_sample = bytes()
            
        time.sleep(0.05)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    _stop_listening(wait_for_stop=False)
    data_queue.queue.clear()
    time.sleep(1)


def process_loop():
    global data_queue
    global source
    global rec
    global main_window
    global pressed

    _text = ""
    _time_last = None
    _last_sample = bytes()

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen", __file__)

    def record_callback(_, audio:sr.AudioData) -> None:
        _data = audio.get_raw_data()
        data_queue.put(_data)

    _stop_listening = rec.listen_in_background(source, record_callback, phrase_time_limit=CONFIG["phrase_time_limit"])

    _time_last = time.time()
    _last_tokens = []
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
                play_sound("clear", __file__)
                clear_chatbox()
                break
            elif _last_sample == bytes():
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "#00008b")
                play_sound("timeout", __file__)
                break
        elif not data_queue.empty():
            while not data_queue.empty():
                data = data_queue.get()
                _last_sample += data

            _torch_audio = torch.from_numpy(np.frombuffer(_last_sample, np.int16).flatten().astype(np.float32) / 32768.0)

            _transcription = transcribe(_torch_audio, _last_tokens)
            _text = _transcription[0]
            _last_tokens = _transcription[1]
                
            _time_last = time.time()
            populate_chatbox(_text, True)
        elif _last_sample != bytes() and time.time() - _time_last > CONFIG["pause_threshold"]:
            main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
            print(_text)
            play_sound("finished", __file__)
            break
        elif _last_sample == bytes() and time.time() - _time_last > CONFIG["timeout_time"]:
            main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "#00008b")
            play_sound("timeout", __file__)
            break
        time.sleep(0.05)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)
    _stop_listening(wait_for_stop=False)
    data_queue.queue.clear()
    time.sleep(0.1)

def process_once():
    global main_window
    global pressed

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen", __file__)
    _torch_audio = listen_once()
    if _torch_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout", __file__)
        set_typing_indicator(False)
    else:
        play_sound("donelisten", __file__)
        set_typing_indicator(True)
        print(_torch_audio)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _trans = transcribe(_torch_audio)[0]
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound("timeout", __file__)
            elif _trans:
                main_window.set_status_label("FINISHED - WAITING FOR INPUT", "blue")
                populate_chatbox(_trans)
                play_sound("finished", __file__)
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound("timeout", __file__)
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout", __file__)

    set_typing_indicator(False)
    main_window.set_button_enabled(True)


def get_ovraction_bstate():
    global action_set_handle
    global button_action_handle
    global application

    _event = openvr.VREvent_t()
    _has_events = True
    while _has_events:
        _has_events = application.pollNextEvent(_event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = action_set_handle
    openvr.VRInput().updateActionState(_actionsets)
    return bool(openvr.VRInput().getDigitalActionData(button_action_handle, openvr.k_ulInvalidInputValueHandle).bState)


def get_trigger_state():
    global ovr_initialized

    if ovr_initialized and get_ovraction_bstate():
        return True
    else:
        return keyboard.is_pressed(CONFIG["hotkey"])


def handle_input():
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
            play_sound("clear", __file__)
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
    global main_window
    global enter_pressed

    enter_pressed = True
    if text:
        populate_chatbox(text, False, True)
        play_sound("finished", __file__)
        main_window.clear_textfield()
    else:
        clear_chatbox()
        play_sound("clear", __file__)


def textfield_keyrelease(text):
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
    global main_window
    global config_ui
    global use_kat
    global osc

    print("Closing...")
    try:
        osc.stop()
        main_window.on_closing()
        config_ui.on_closing()
    except Exception as e:
        print(e)


def settings_closing(save=False):
    global osc
    global config_ui
    global config_ui_open

    if save:
        osc.stop()
        config_ui.save()
        config_ui.on_closing()
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
    global config_ui

    config_ui.set_energy_threshold("Be quiet for 5 seconds...")
    with source:
        _last = rec.energy_threshold
        rec.adjust_for_ambient_noise(source, 5)
        value = round(rec.energy_threshold) + 20
        rec.energy_threshold = _last
        config_ui.set_energy_threshold(str(value))


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
main_window.create_loop(50, handle_input)
main_window.open()
