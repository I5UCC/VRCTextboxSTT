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


VRC_INPUT_PARAM = "/chatbox/input"
VRC_TYPING_PARAM = "/chatbox/typing"
ACTIONSETHANDLE = "/actions/textboxstt"
STTLISTENHANDLE = "/actions/textboxstt/in/sttlisten"
logfile = get_absolute_path('out.log')
config = json.load(open(get_absolute_path('config.json')))

open(logfile, 'w').close()
log = logging.getLogger('TextboxSTT')
sys.stdout = StreamToLogger(log, logging.INFO, logfile)
sys.stderr = StreamToLogger(log, logging.ERROR, logfile)


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


ui = UI("v0.3.1", config["IP"], config["Port"], get_sound_devices(), config["microphone_index"])

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


def play_sound(filename):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


oscClient = udp_client.SimpleUDPClient(config["IP"], int(config["Port"]))

model = config["model"].lower()
lang = config["language"].lower()
if model != "large" and lang == "english" and ".en" not in model:
    model = model + ".en"
ui.set_status_label(f"LOADING \"{model}\" MODEL", "orange")
# Temporarily output stderr to text label for download progress.
sys.stderr.write = ui.loading_status
# Load Whisper model
audio_model = whisper.load_model(model, download_root=get_absolute_path("whisper_cache/"), in_memory=True)

sys.stderr = StreamToLogger(log, logging.ERROR, logfile)

# load the speech recognizer and set the initial energy threshold and pause threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = bool(config["dynamic_energy_threshold"])
r.energy_threshold = int(config["energy_threshold"])
r.pause_threshold = float(config["pause_threshold"])

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

ui.set_conf_label(config["IP"], config["Port"], ovr_initialized, str(audio_model.device))


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
            audio = r.listen(source, timeout=float(config["timeout_time"]))
        except sr.WaitTimeoutError:
            return None

        return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


def transcribe(torch_audio, language):
    if language:
        result = audio_model.transcribe(torch_audio, language=language)
    else:
        result = audio_model.transcribe(torch_audio)
    return result["text"].strip()


def clear_chatbox():
    ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
    oscClient.send_message(VRC_INPUT_PARAM, ["", True, False])
    oscClient.send_message(VRC_TYPING_PARAM, False)
    ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
    ui.set_text_label("- No Text -")


def populate_chatbox(text):
    ui.set_text_label(text)
    print("Transcribed: " + text)
    ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
    oscClient.send_message(VRC_INPUT_PARAM, [text, True, True])
    oscClient.send_message(VRC_TYPING_PARAM, False)
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
        return keyboard.is_pressed(config["hotkey"])


def process_stt():
    global held
    oscClient.send_message(VRC_TYPING_PARAM, True)

    ui.set_status_label("LISTENING", "#FF00FF")
    play_sound("listen")
    torch_audio = listen()
    if torch_audio is None:
        ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
        play_sound("timeout")
        oscClient.send_message(VRC_TYPING_PARAM, False)
        held = True
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


def handle_input():
    global thread_process
    global held
    pressed = get_trigger_state()
    curr_time = time.time()

    if thread_process.is_alive():
        return
    elif pressed and not held:
        while pressed:
            if time.time() - curr_time > float(config["hold_time"]):
                clear_chatbox()
                play_sound("clear")
                held = True
                break
            pressed = get_trigger_state()
            ui.update()
            time.sleep(0.05)
        if not held:
            thread_process = threading.Thread(target=process_stt)
            thread_process.start()
    elif held and not pressed:
        held = False


def on_closing():
    config["microphone_index"] = get_audiodevice_index()
    json.dump(config, open(get_absolute_path('config.json'), "w"), indent=4)
    ui.tkui.destroy()


held = False
thread_process = threading.Thread(target=process_stt)
ui.set_status_label("WAITING FOR INPUT", "#00008b")
ui.tkui.protocol("WM_DELETE_WINDOW", on_closing)
ui.create_loop(50, handle_input)
ui.tkui.mainloop()
