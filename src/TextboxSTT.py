import os
import sys
import json
import logging
from StreamToLogger import StreamToLogger


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


VERSION = "v0.5"
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

import threading
import time
import keyboard
import numpy as np
import winsound
from pythonosc import udp_client
import speech_recognition as sr
import openvr
import whisper
import torch
import re
from katosc import KatOsc
from CustomThread import CustomThread
from UI import UI
from settings_UI import settings_ui

osc_client = None
kat = None
textbox = True
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

def init():
    global ui
    global osc_client
    global kat
    global textbox
    global model
    global language
    global use_cpu
    global rec
    global ovr_initialized
    global application
    global action_set_handle
    global button_action_handle

    osc_client = udp_client.SimpleUDPClient(CONFIG["osc_ip"], int(CONFIG["osc_port"]))
    textbox = bool(CONFIG["use_textbox"])
    if CONFIG["use_kat"]:
        _kat_sync = False if CONFIG["kat_sync"] else True
        print(_kat_sync)
        kat =  KatOsc(osc_client, CONFIG["osc_ip"], CONFIG["osc_server_port"], _kat_sync, 4 if _kat_sync else int(CONFIG["kat_sync"]))
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
        sys.stderr.write = ui.loading_status
    else:
        print("Whisper model already in cache.")

    ui.set_status_label(f"LOADING \"{_whisper_model}\" MODEL", "orange")
    # Load Whisper model
    model = whisper.load_model(_whisper_model, download_root=get_absolute_path("whisper_cache/"), in_memory=True)
    sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)
    use_cpu = True if str(model.device) == "cpu" else False

    # load the speech recognizer and set the initial energy threshold and pause threshold
    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = bool(CONFIG["dynamic_energy_threshold"])
    rec.energy_threshold = int(CONFIG["energy_threshold"])
    rec.pause_threshold = float(CONFIG["pause_threshold"])

    # Initialize OpenVR
    ui.set_status_label("INITIALIZING OVR", "orange")
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
        ui.set_status_label("INITIALZIED OVR", "green")
    except Exception:
        ovr_initialized = False
        ui.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "red")

    ui.set_conf_label(CONFIG["osc_ip"], CONFIG["osc_port"], ovr_initialized, use_cpu)
    ui.set_status_label("INITIALIZED - WAITING FOR INPUT", "green")


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

    if result:
        result = result.text.strip()
        # Filter by banned words
        for word in CONFIG["banned_words"]:
            tmp = re.compile(word, re.IGNORECASE)
            result = tmp.sub("", result)
        result = re.sub(' +', ' ', result)

    return result


def clear_chatbox():
    global textbox
    global kat

    ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    if textbox:
        osc_client.send_message(VRC_INPUT_PARAM, ["", True, False])
        osc_client.send_message(VRC_TYPING_PARAM, False)
    if kat:
        kat.clear()
        kat.hide()
    ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    ui.set_text_label("- No Text -")


def set_typing_indicator(b: bool):
    global textbox
    global kat

    if textbox:
        osc_client.send_message(VRC_TYPING_PARAM, b)
    if kat:
        osc_client.send_message(AV_LISTENING_PARAM, b)


def populate_chatbox(text):
    global ui
    global textbox
    global kat

    text = text[:VRC_INPUT_CHARLIMIT]
    ui.set_text_label(text)
    print("Transcribed: " + text)
    ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
    if textbox:
        osc_client.send_message(VRC_INPUT_PARAM, [text, True, True])
    if kat:
        kat.set_text(text[:KAT_CHARLIMIT])
    set_typing_indicator(False)
    ui.set_status_label("WAITING FOR INPUT", "#00008b")


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
    global ui
    global pressed

    ui.set_button_enabled(False)
    set_typing_indicator(True)
    ui.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    _torch_audio = listen()
    if _torch_audio is None:
        ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        set_typing_indicator(False)
    else:
        play_sound("donelisten")
        set_typing_indicator(True)
        print(_torch_audio)
        ui.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            _trans = transcribe(_torch_audio)
            if pressed:
                ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound("timeout")
            elif _trans:
                populate_chatbox(_trans)
                play_sound("finished")
            else:
                ui.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound("timeout")
        else:
            ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout")
    
    set_typing_indicator(False)
    ui.set_button_enabled(True)


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


def main_window_closing():
    global ui
    global kat

    print("Closing...")
    kat.stop()
    ui.on_closing()
    config_ui.on_closing()


def entrybox_enter_event(text):
    global ui

    if text:
        populate_chatbox(text)
        play_sound("finished")
        ui.clear_textfield()
    else:
        clear_chatbox()
        play_sound("clear")


def settings_closing():
    global kat
    global config_ui
    global config_ui_open

    config_ui_open = False
    kat.stop()
    config_ui.on_closing()
    ui.set_button_enabled(True)
    init()


def open_settings():
    global ui
    global config_ui
    global config_ui_open
    ui.set_status_label("WAITING FOR SETTINGS MENU TO CLOSE", "orange")
    config_ui_open = True
    config_ui = settings_ui(CONFIG, CONFIG_PATH)
    config_ui.tkui.protocol("WM_DELETE_WINDOW", settings_closing)
    ui.set_button_enabled(False)
    config_ui.open()


ui = UI(VERSION, CONFIG["osc_ip"], CONFIG["osc_port"])
init()

ui.tkui.protocol("WM_DELETE_WINDOW", main_window_closing)
ui.textfield.bind("<Return>", (lambda event: entrybox_enter_event(ui.textfield.get())))
ui.textfield.bind("<Key>", (lambda event: set_typing_indicator(True)))
ui.btn_settings.configure(command=open_settings)
ui.create_loop(50, handle_input)
ui.open()
