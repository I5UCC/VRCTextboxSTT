import os
import sys
import json
import logging
import pyaudio
from UI import UI
from StreamToLogger import StreamToLogger


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


VERSION = "v0.4"
VRC_INPUT_CHARLIMIT = 144
KAT_CHARLIMIT = 128
VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
AV_LISTENING_PARAM = "/avatar/parameters/stt_listening"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
LOGFILE = get_absolute_path('out.log')
CONFIG = json.load(open(get_absolute_path('config.json')))

open(LOGFILE, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = StreamToLogger(log, logging.INFO, LOGFILE)
sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)


def get_sound_devices():
    res = ["Default"]
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdev = info.get("deviceCount")

    for i in range(0, numdev):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            res.append([i, p.get_device_info_by_host_api_device_index(0, i).get('name')])
            print(f"Input Device id {i} - {p.get_device_info_by_host_api_device_index(0, i).get('name')}")

    return res


ui = UI(VERSION, CONFIG["osc_ip"], CONFIG["osc_port"], get_sound_devices(), CONFIG["microphone_index"])

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


oscClient = udp_client.SimpleUDPClient(CONFIG["osc_ip"], int(CONFIG["osc_port"]))
kat = None
textbox = bool(CONFIG["use_textbox"])
if CONFIG["use_kat"]:
    kat =  KatOsc(oscClient, CONFIG["osc_ip"], CONFIG["osc_server_port"], True)

model = CONFIG["model"].lower()
lang = CONFIG["language"].lower()
if lang == "":
    lang = None
elif model != "large" and lang == "english" and ".en" not in model:
    model = model + ".en"
ui.set_status_label(f"LOADING \"{model}\" MODEL", "orange")
# Temporarily output stderr to text label for download progress.
sys.stderr.write = ui.loading_status
# Load Whisper model
model = whisper.load_model(model, download_root=get_absolute_path("whisper_cache/"), in_memory=True)
use_cpu = True if str(model.device) == "cpu" else False

sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)

# load the speech recognizer and set the initial energy threshold and pause threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = bool(CONFIG["dynamic_energy_threshold"])
r.energy_threshold = int(CONFIG["energy_threshold"])
r.pause_threshold = float(CONFIG["pause_threshold"])

# Initialize OpenVR
ui.set_status_label("INITIALIZING OVR", "orange")
ovr_initialized = False
try:
    application = openvr.init(openvr.VRApplication_Utility)
    action_path = get_absolute_path("bindings/textboxstt_actions.json")
    appmanifest_path = get_absolute_path("app.vrmanifest")
    openvr.VRApplications().addApplicationManifest(appmanifest_path)
    openvr.VRInput().setActionManifestPath(action_path)
    actionSetHandle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
    buttonactionhandle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
    ovr_initialized = True
    ui.set_status_label("INITIALZIED", "green")
except Exception:
    ovr_initialized = False
    ui.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "red")

ui.set_conf_label(CONFIG["osc_ip"], CONFIG["osc_port"], ovr_initialized, use_cpu)


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


def get_audiodevice_index():
    option = ui.value_inside.get()
    if option != "Default":
        return int(option[1:option.index(',')])
    else:
        return None


def listen():
    device_index = get_audiodevice_index()
    with sr.Microphone(device_index, sample_rate=16000) as source:
        try:
            audio = r.listen(source, timeout=float(CONFIG["timeout_time"]))
        except sr.WaitTimeoutError:
            return None

        return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def transcribe(torch_audio, language):
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
    ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    if textbox:
        oscClient.send_message(VRC_INPUT_PARAM, ["", True, False])
        oscClient.send_message(VRC_TYPING_PARAM, False)
    if kat:
        kat.clear()
        kat.hide()
    ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    ui.set_text_label("- No Text -")


def set_typing_indicator(b: bool):
    if textbox:
        oscClient.send_message(VRC_TYPING_PARAM, b)
    if kat:
        oscClient.send_message(AV_LISTENING_PARAM, b)


def populate_chatbox(text):
    text = text[:VRC_INPUT_CHARLIMIT]
    ui.set_text_label(text)
    print("Transcribed: " + text)
    ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
    if textbox:
        oscClient.send_message(VRC_INPUT_PARAM, [text[:VRC_INPUT_CHARLIMIT], True, True])
    if kat:
        kat.set_text(text[:KAT_CHARLIMIT])
    set_typing_indicator(False)
    ui.set_status_label("WAITING FOR INPUT", "#00008b")


def get_ovraction_bstate():
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(_actionsets)
    return bool(openvr.VRInput().getDigitalActionData(buttonactionhandle, openvr.k_ulInvalidInputValueHandle).bState)


def get_trigger_state():
    if ovr_initialized and get_ovraction_bstate():
        return True
    else:
        return keyboard.is_pressed(CONFIG["hotkey"])


def process_stt():
    global pressed

    set_typing_indicator(True)
    ui.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    torch_audio = listen()
    if torch_audio is None:
        ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        set_typing_indicator(False)
    else:
        play_sound("donelisten")
        set_typing_indicator(True)
        print(torch_audio)
        ui.set_status_label("TRANSCRIBING", "orange")

        if not pressed:
            trans = transcribe(torch_audio, lang)
            if pressed:
                ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                play_sound("timeout")
            elif trans:
                populate_chatbox(trans)
                play_sound("finished")
            else:
                ui.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                play_sound("timeout")
        else:
            ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout")
    
    set_typing_indicator(False)


def handle_input():
    global thread_process
    global held
    global holding
    global pressed
    global curr_time

    pressed = get_trigger_state()

    if thread_process.is_alive():
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


def on_closing():
    CONFIG["microphone_index"] = get_audiodevice_index()
    json.dump(CONFIG, open(get_absolute_path('config.json'), "w"), indent=4)
    kat.stop()
    ui.tkui.destroy()


def entrybox_enter_event(text):
    if text:
        populate_chatbox(text)
        play_sound("finished")
        ui.clear_textfield()
    else:
        clear_chatbox()
        play_sound("clear")


curr_time = 0.0
pressed = False
holding = False
held = False
thread_process = threading.Thread(target=process_stt)

ui.set_status_label("WAITING FOR INPUT", "#00008b")
ui.tkui.protocol("WM_DELETE_WINDOW", on_closing)
ui.textfield.bind("<Return>", (lambda event: entrybox_enter_event(ui.textfield.get())))
ui.textfield.bind("<Key>", (lambda event: set_typing_indicator(True)))
ui.create_loop(50, handle_input)
ui.tkui.mainloop()
