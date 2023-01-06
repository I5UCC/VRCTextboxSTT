import sys
import logging

# Initialize logging and UI before starting.
from StreamToLogger import StreamToLogger
log = logging.getLogger('TextboxSTT')
sys.stdout = StreamToLogger(log,logging.INFO)
sys.stderr = StreamToLogger(log,logging.ERROR)
from UI import UI
ui = UI()

import os
import time
import json
import keyboard
import numpy as np
import winsound
from pythonosc import udp_client
import speech_recognition as sr
import openvr
import whisper
import torch


VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
held = False


def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


config = json.load(open(get_absolute_path('config.json')))
ui.set_conf_label(config["IP"], config["Port"])
oscClient = udp_client.SimpleUDPClient(config["IP"], int(config["Port"]))

# Load Whisper model
model = config["model"].lower()
lang = config["language"].lower()
if model != "large" and lang == "english" and ".en" not in model:
        model = model + ".en"
ui.set_status_label(f"LOADING \"{model}\" MODEL", "orange")
audio_model = whisper.load_model(model);

#load the speech recognizer and set the initial energy threshold and pause threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = bool(config["dynamic_energy_threshold"])
r.energy_threshold = int(config["energy_threshold"])
r.pause_threshold = float(config["pause_threshold"])

# Initialize OpenVR
ui.set_status_label(f"INITIALIZING OVR", "orange")
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
    ui.set_status_label("OVR ERROR", "red")


def listen(device_index = None):
    with sr.Microphone(device_index, sample_rate=16000) as source:
        try:
            audio = r.listen(source, timeout=float(config["timeout_time"]))
        except sr.WaitTimeoutError:
            return None
        
        return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def transcribe(torch_audio, language):
        ui.set_status_label("TRANSCRIBING", "orange")
        if language:
            result = audio_model.transcribe(torch_audio, language=language)
        else:
            result = audio_model.transcribe(torch_audio)
        return result["text"]


def clear_chatbox():
    ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    oscClient.send_message(VRC_INPUT_PARAM, ["", True, False])
    oscClient.send_message(VRC_TYPING_PARAM, False)
    ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    ui.set_text_label("- No Text -")


def populate_chatbox(text):
    ui.set_text_label(text)
    print(text)
    ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
    oscClient.send_message(VRC_INPUT_PARAM, [text, True, True])
    oscClient.send_message(VRC_TYPING_PARAM, False)
    ui.set_status_label("WAITING FOR INPUT", "#00008b")


def process():
    global held
    oscClient.send_message(VRC_TYPING_PARAM, True)

    ui.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    torch_audio = listen()
    if torch_audio is None:
        ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        oscClient.send_message(VRC_TYPING_PARAM, False)
    else:
        play_sound("donelisten")
        oscClient.send_message(VRC_TYPING_PARAM, True)
        print(torch_audio)
        ui.set_status_label("TRANSCRIBING", "orange")
        trans = transcribe(torch_audio, lang)[:144]
        if not get_trigger_state() and trans:
            play_sound("finished")
            populate_chatbox(trans)
        else:
            ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
            play_sound("timeout")
            held = True


def get_trigger_state():
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(_actionsets)

    if bool(openvr.VRInput().getDigitalActionData(buttonactionhandle, openvr.k_ulInvalidInputValueHandle).bState):
        return True
    else:
        return keyboard.is_pressed(config["hotkey"])


def handle_ovr_input():
    global held
    pressed = get_trigger_state()
    curr_time = time.time()

    if pressed and not held:
        while pressed:
            if time.time() - curr_time > float(config["hold_time"]):
                clear_chatbox()
                held = True
                break
            pressed = get_trigger_state()
            ui.update()
            time.sleep(0.05)
        if not held:
            process()
    elif held and not pressed:
        held = False

    ui.tkui.after(50, handle_ovr_input)

if ovr_initialized:
    ui.tkui.after(50, handle_ovr_input)

ui.set_status_label("WAITING FOR INPUT", "#00008b")
ui.tkui.mainloop()
