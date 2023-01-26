import os
import sys
import json
import logging
from streamtologger import StreamToLogger
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


VERSION = "v0.6"
VRC_INPUT_CHARLIMIT = 144
KAT_CHARLIMIT = 128
VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
AV_LISTENING_PARAM = "/avatar/parameters/stt_listening"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
LOGFILE = get_absolute_path('out.log')
CONFIG_PATH = get_absolute_path('config.json')
CONFIG = json.load(open(CONFIG_PATH))

open(LOGFILE, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = StreamToLogger(log, logging.INFO, LOGFILE)
sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)


def loadfont(fontpath, private=True, enumerable=False):
    '''
    Makes fonts located in file `fontpath` available to the font system.

    `private`     if True, other processes cannot see this font, and this
                  font will be unloaded when the process dies
    `enumerable`  if True, this font will appear when enumerating fonts

    See https://msdn.microsoft.com/en-us/library/dd183327(VS.85).aspx

    '''
    # This function was taken from
    # https://github.com/ifwe/digsby/blob/f5fe00244744aa131e07f09348d10563f3d8fa99/digsby/src/gui/native/win/winfonts.py#L15
    # "Copyright (c) 2006-2012 Tagged, Inc; All Rights Reserved"
    FR_PRIVATE  = 0x10
    FR_NOT_ENUM = 0x20

    if isinstance(fontpath, bytes):
        pathbuf = create_string_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExA
    elif isinstance(fontpath, str):
        pathbuf = create_unicode_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExW
    else:
        raise TypeError('fontpath must be of type str or bytes')

    flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
    num_fonts_added = add_font_resource_ex(byref(pathbuf), flags, 0)
    return bool(num_fonts_added)


if os.name == 'nt':
    loadfont(get_absolute_path("resources/CascadiaCode.ttf"))


import threading
import time
import keyboard
import numpy as np
from pythonosc import udp_client
import winsound
import speech_recognition as sr
import openvr
import whisper
import torch
import re
from katosc import KatOsc
from customthread import CustomThread
from ui import MainWindow, SettingsWindow


osc_client = None
kat = None
use_kat = True
use_textbox = True
use_both = True
model = "base"
language = "english"
use_cpu = False
rec = None
ovr_initialized = False
application = None
action_set_handle = None
button_action_handle = None
curr_time = 0.0
pressed = False
holding = False
held = False
thread_process = threading.Thread()
config_ui = None
config_ui_open = False
enter_pressed = False


def init():
    global main_window
    global osc_client
    global kat
    global use_textbox
    global use_kat
    global use_both
    global model
    global language
    global use_cpu
    global rec
    global ovr_initialized
    global application
    global action_set_handle
    global button_action_handle

    osc_client = udp_client.SimpleUDPClient(CONFIG["osc_ip"], int(CONFIG["osc_port"]))
    use_textbox = bool(CONFIG["use_textbox"])
    use_kat = bool(CONFIG["use_kat"])
    use_both = bool(CONFIG["use_both"])
    if use_kat:
        _kat_sync = False if CONFIG["kat_sync"] else True
        kat = KatOsc(osc_client, CONFIG["osc_ip"], CONFIG["osc_server_port"], _kat_sync, None if _kat_sync else int(CONFIG["kat_sync"]))
    else:
        kat = None

    _whisper_model = CONFIG["model"].lower()
    language = CONFIG["language"].lower()
    if language == "":
        language = None
    elif _whisper_model != "large" and language == "english" and ".en" not in _whisper_model:
        _whisper_model = _whisper_model + ".en"

    # Temporarily output stderr to text label for download progress.
    if not os.path.isfile(get_absolute_path(f"whisper_cache/{_whisper_model}.pt")):
        sys.stderr.write = main_window.loading_status
    else:
        print("Whisper model already in cache.")

    main_window.set_status_label(f"LOADING \"{_whisper_model}\" MODEL", "orange")
    # Load Whisper model
    device = "cpu" if bool(CONFIG["use_cpu"]) or not torch.cuda.is_available() else "cuda"
    model = whisper.load_model(_whisper_model, download_root=get_absolute_path("whisper_cache/"), in_memory=True, device=device)
    sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)
    use_cpu = True if str(model.device) == "cpu" else False

    # load the speech recognizer and set the initial energy threshold and pause threshold
    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = bool(CONFIG["dynamic_energy_threshold"])
    rec.energy_threshold = int(CONFIG["energy_threshold"])
    rec.pause_threshold = float(CONFIG["pause_threshold"])

    # Initialize OpenVR
    main_window.set_status_label("INITIALIZING OVR", "orange")
    ovr_initialized = False
    try:
        application = openvr.init(openvr.VRApplication_Utility)
        action_path = get_absolute_path("bindings/textboxstt_actions.json")
        appmanifest_path = get_absolute_path("app.vrmanifest")
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


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


def get_audiodevice_index():
    option = CONFIG["microphone_index"]
    if option:
        return int(option)
    else:
        return None


def listen():
    global rec

    device_index = get_audiodevice_index()
    with sr.Microphone(device_index, sample_rate=16000) as source:
        try:
            audio = rec.listen(source, timeout=float(CONFIG["timeout_time"]))
        except sr.WaitTimeoutError:
            return None

        return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def filter_banned_words(text):
    if not text:
        return None

    text = text.strip()
    print(CONFIG["banned_words"] is None)
    if CONFIG["banned_words"] is None:
        return text

    for word in CONFIG["banned_words"]:
        tmp = re.compile(word, re.IGNORECASE)
        text = tmp.sub("", text)
    text = re.sub(' +', ' ', text)
    return text


def transcribe(torch_audio):
    global use_cpu
    global language
    global model

    use_gpu = not use_cpu
    torch_audio = whisper.pad_or_trim(torch_audio)
    options = whisper.DecodingOptions(language=language, fp16=use_gpu, without_timestamps=True)
    mel = whisper.log_mel_spectrogram(torch_audio).to(model.device)
    t = CustomThread(target=whisper.decode, args=[model, mel, options])
    t.start()

    timeout = float(CONFIG["max_transcribe_time"])
    if timeout == 0.0:
        timeout = None
    result = t.join(timeout)

    return filter_banned_words(result.text)


def clear_chatbox():
    global use_textbox
    global use_kat
    global use_both
    global kat

    main_window.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    main_window.clear_textfield()
    if use_textbox and use_both or use_textbox and use_kat and not kat.isactive or not use_kat:
        osc_client.send_message(VRC_INPUT_PARAM, ["", True, False])
        osc_client.send_message(VRC_TYPING_PARAM, False)
    if use_kat and kat.isactive:
        kat.clear()
        kat.hide()
    main_window.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    main_window.set_text_label("- No Text -")


def set_typing_indicator(state: bool, textfield: bool = False):
    global use_textbox
    global use_kat
    global use_both
    global kat

    if use_textbox and use_both or use_textbox and use_kat and not kat.isactive or not use_kat:
        osc_client.send_message(VRC_TYPING_PARAM, state)
    if use_kat and kat.isactive and not textfield:
        osc_client.send_message(AV_LISTENING_PARAM, state)


def populate_chatbox(text):
    global main_window
    global use_textbox
    global use_kat
    global use_both
    global kat

    text = text[:VRC_INPUT_CHARLIMIT]
    main_window.set_text_label(text)
    main_window.set_status_label("POPULATING TEXTBOX", "#ff8800")
    if use_textbox and use_both or use_textbox and use_kat and not kat.isactive or not use_kat:
        osc_client.send_message(VRC_INPUT_PARAM, [text, True, True])
    if use_kat and kat.isactive:
        kat.set_text(text[:KAT_CHARLIMIT])
    set_typing_indicator(False)
    main_window.set_status_label("WAITING FOR INPUT", "#00008b")


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


def process_stt():
    global main_window
    global pressed

    main_window.set_button_enabled(False)
    set_typing_indicator(True)
    main_window.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    _torch_audio = listen()
    if _torch_audio is None:
        main_window.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        set_typing_indicator(False)
    else:
        play_sound("donelisten")
        set_typing_indicator(True)
        print(_torch_audio)
        main_window.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _trans = transcribe(_torch_audio)
            if pressed:
                main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound("timeout")
            elif _trans:
                populate_chatbox(_trans)
                play_sound("finished")
            else:
                main_window.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound("timeout")
        else:
            main_window.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout")

    set_typing_indicator(False)
    main_window.set_button_enabled(True)


def handle_input():
    global thread_process
    global held
    global holding
    global pressed
    global curr_time
    global config_ui_open

    pressed = get_trigger_state()

    if thread_process.is_alive() or config_ui_open:
        return
    elif pressed and not holding and not held:
        holding = True
        curr_time = time.time()
    elif pressed and holding and not held:
        holding = True
        if time.time() - curr_time > float(CONFIG["hold_time"]):
            clear_chatbox()
            play_sound("clear")
            held = True
            holding = False
    elif not pressed and holding and not held:
        held = True
        holding = False
        thread_process = threading.Thread(target=process_stt)
        thread_process.start()
    elif not pressed and held:
        held = False
        holding = False


def entrybox_enter_event(text):
    global main_window
    global enter_pressed

    enter_pressed = True
    if text:
        populate_chatbox(text)
        play_sound("finished")
        main_window.clear_textfield()
    else:
        clear_chatbox()
        play_sound("clear")


def textfield_keyrelease(text):
    global kat
    global use_kat
    global enter_pressed

    if not enter_pressed:
        if len(text) > VRC_INPUT_CHARLIMIT:
            main_window.textfield.delete(VRC_INPUT_CHARLIMIT, len(text))
            main_window.textfield.icursor(VRC_INPUT_CHARLIMIT)
        _is_text_empty = text == ""
        set_typing_indicator(not _is_text_empty, True)
        if use_kat and kat.isactive:
            if _is_text_empty:
                kat.clear()
                kat.hide()
                main_window.set_text_label("- No Text -")
            else:
                text = text[:VRC_INPUT_CHARLIMIT]
                kat.set_text(text)
                main_window.set_text_label(text)
    
    enter_pressed = False


def main_window_closing():
    global main_window
    global use_kat
    global kat

    print("Closing...")
    if use_kat:
        kat.stop()
    main_window.on_closing()
    config_ui.on_closing()


def settings_closing(save=False):
    global kat
    global config_ui
    global config_ui_open

    if save:
        if use_kat:
            kat.stop()
        config_ui.save()
        try:
            init()
        except Exception as e:
            print(e)
            main_window.set_status_label("ERROR INITIALIZING, PLEASE CHECK YOUR SETTINGS,\nLOOK INTO out.log for more info on the error", "red")
    else:
        main_window.set_status_label("SETTINGS NOT SAVED - WAITING FOR INPUT", "#00008b")
    
    main_window.set_button_enabled(True)
    config_ui_open = False
    config_ui.on_closing()


def open_settings():
    global main_window
    global config_ui
    global config_ui_open

    main_window.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = SettingsWindow(CONFIG, CONFIG_PATH)
    config_ui.btn_save.configure(command=(lambda: settings_closing(True)))
    config_ui.tkui.protocol("WM_DELETE_WINDOW", settings_closing)
    main_window.set_button_enabled(False)
    config_ui.open()


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
