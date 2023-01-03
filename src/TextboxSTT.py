import sys
import logging

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        filename='out.log',
        filemode='a'
        )
log = logging.getLogger('TextboxSTT')
sys.stdout = StreamToLogger(log,logging.INFO)
sys.stderr = StreamToLogger(log,logging.ERROR)

import os
import traceback
import time
import json
import keyboard
import numpy as np
import winsound
import openvr
import whisper
import torch
import speech_recognition as sr
import tkinter as tk
from pythonosc import udp_client

ui = tk.Tk()
ui.minsize(810, 310)
ui.maxsize(810, 310)
ui.resizable(False, False)
ui.configure(bg="#333333")
ui.title("TextboxSTT")

status_lbl = tk.Label(ui, text="Status")
status_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 12))
status_lbl.place(relx=0.045, rely=0.07, anchor="w")

color_lbl = tk.Label(ui, text="")
color_lbl.configure(bg="blue", width=2, fg="white", font=("Cascadia Code", 12))
color_lbl.place(relx=0.01, rely=0.07, anchor="w")

text_lbl = tk.Label(ui, wraplength=800, text="---")
text_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 27))
text_lbl.place(relx=0.5, rely=0.55, anchor="center")

def set_status_label(text, color):
    status_lbl.configure(text=text)
    color_lbl.configure(bg=color)

def set_text_label(text):
    text = text[:144]
    text_lbl.configure(text=text)

VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"

def cls():
    """Clears Console"""
    os.system('cls' if os.name == 'nt' else 'clear')


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

model = config["model"].lower()
lang = config["language"].lower()
is_english = lang == "english"

if model != "large" and is_english:
        model = model + ".en"
audio_model = whisper.load_model(model);

#load the speech recognizer and set the initial energy threshold and pause threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = bool(config["dynamic_energy_threshold"])
r.energy_threshold = int(config["energy_threshold"])
r.pause_threshold = float(config["pause_threshold"])

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
except Exception:
    ovr_initialized = False


def listen_and_transcribe():
    with sr.Microphone(sample_rate=16000) as source:
        print("LISTENING")
        set_status_label("LISTENING", "#FF00FF")
        play_sound("listen")
        try:
            audio = r.listen(source, timeout=float(config["timeout_time"]))
        except sr.WaitTimeoutError:
            clear_chatbox()
            print("TIMEOUT")
            play_sound("timeout")
            return None
        play_sound("donelisten")
        torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
        
        oscClient.send_message(VRC_TYPING_PARAM, True)
        print("TRANSCRIBING")
        set_status_label("TRANSCRIBING", "orange")
        if lang:
            result = audio_model.transcribe(torch_audio, language=lang)
        else:
            result = audio_model.transcribe(torch_audio)
        play_sound("finished")
        return result["text"]


def send_message():
    oscClient.send_message(VRC_TYPING_PARAM, True)
    trans = listen_and_transcribe()
    if trans:
        print("-" + trans)
        set_text_label(trans)
        print("POPULATING TEXTBOX")
        set_status_label("TRANSCRIBING", "#ff8800")
        oscClient.send_message(VRC_INPUT_PARAM, [trans, True, True])
        oscClient.send_message(VRC_TYPING_PARAM, False)
        print("WAITING")
        set_status_label("WAITING", "#00008b")


def clear_chatbox():
    print("CLEARING OSC TEXTBOX")
    set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    oscClient.send_message(VRC_INPUT_PARAM, ["", True])
    oscClient.send_message(VRC_TYPING_PARAM, False)
    print("WAITING")
    set_status_label("WAITING", "#00008b")
    set_text_label("---")


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

    ui.after(50, handle_input)


held = False
keyboard.add_hotkey(config["record_hotkey"], send_message)
keyboard.add_hotkey(config["clear_hotkey"], clear_chatbox)
cls()
print("-INITIALZIED-")
set_status_label("INITIALZIED", "green")
print("WAITING")
set_status_label("WAITING", "#00008b")
if ovr_initialized:
    try:
        ui.after(50, handle_input)
    except Exception:
        cls()
        print("UNEXPECTED ERROR\n")
        print("Please Create an Issue on GitHub with the following information:\n")
        traceback.print_exc()
        input("\nPress ENTER to exit")
        sys.exit()
else:
    print("OpenVR couldnt be initialized, continuing PC only mode.")

ui.mainloop()
