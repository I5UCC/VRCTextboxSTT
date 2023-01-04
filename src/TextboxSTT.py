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

def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


config = json.load(open(get_absolute_path('config.json')))

oscClient = udp_client.SimpleUDPClient(config["IP"], int(config["Port"]))

# Load Whisper model
model = config["model"].lower()
lang = config["language"].lower()
if model != "large" and lang == "english":
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

def listen_and_transcribe():
    with sr.Microphone(sample_rate=16000) as source:
        ui.set_status_label("LISTENING", "#FF00FF")
        play_sound("listen")
        try:
            audio = r.listen(source, timeout=float(config["timeout_time"]))
        except sr.WaitTimeoutError:
            ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
            play_sound("timeout")
            return None
        play_sound("donelisten")
        torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
        
        oscClient.send_message(VRC_TYPING_PARAM, True)

        ui.set_status_label("TRANSCRIBING", "orange")
        if lang:
            result = audio_model.transcribe(torch_audio, language=lang)
        else:
            result = audio_model.transcribe(torch_audio)
        play_sound("finished")
        return result["text"][:144]


def send_message():
    oscClient.send_message(VRC_TYPING_PARAM, True)
    trans = listen_and_transcribe()
    if trans:
        ui.set_text_label(trans)
        print(trans)
        ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
        oscClient.send_message(VRC_INPUT_PARAM, [trans, True, True])
        oscClient.send_message(VRC_TYPING_PARAM, False)
        ui.set_status_label("WAITING FOR INPUT", "#00008b")


def clear_chatbox():
    ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    oscClient.send_message(VRC_INPUT_PARAM, ["", True])
    oscClient.send_message(VRC_TYPING_PARAM, False)
    ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    ui.set_text_label("- No Text -")


def get_action_bstate():
    event = openvr.VREvent_t()
    has_events = True
    while has_events:
        has_events = application.pollNextEvent(event)
    _actionsets = (openvr.VRActiveActionSet_t * 1)()
    _actionset = _actionsets[0]
    _actionset.ulActionSet = actionSetHandle
    openvr.VRInput().updateActionState(_actionsets)
    return bool(openvr.VRInput().getDigitalActionData(buttonactionhandle, openvr.k_ulInvalidInputValueHandle).bState)


def handle_input():
    global held
    # Set up OpenVR events and Action sets
    
    pressed = get_action_bstate()
    curr_time = time.time()

    if pressed and not held:
        while pressed:
            if time.time() - curr_time > float(config["hold_time"]):
                clear_chatbox()
                held = True
                break
            pressed = get_action_bstate()
            ui.update()
            time.sleep(0.05)
        if not held:
            send_message()
    elif held and not pressed:
        held = False

    ui.ui.after(50, handle_input)


held = False
keyboard.add_hotkey(config["record_hotkey"], send_message)
keyboard.add_hotkey(config["clear_hotkey"], clear_chatbox)
ui.set_status_label("WAITING FOR INPUT", "#00008b")
if ovr_initialized:
    ui.ui.after(50, handle_input)

ui.ui.mainloop()
