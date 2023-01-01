import speech_recognition as sr
import whisper
import torch
import numpy as np
from pythonosc import udp_client
import json
import winsound
import warnings
import os
import sys

warnings.filterwarnings("ignore", category=UserWarning)

def get_absolute_path(relative_path):
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def play_ping():
    """Plays a ping sound."""
    winsound.PlaySound('ping.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

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

def record_and_transcribe():
    with sr.Microphone(sample_rate=16000) as source:
        print("Recording...")
        play_ping()
        audio = r.listen(source)

        torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)

        print("Transcribing...")
        if lang:
            result = audio_model.transcribe(torch_audio, language=lang)
        else:
            result = audio_model.transcribe(torch_audio)

        return result["text"]

oscClient.send_message("/chatbox/typing", True)
trans = record_and_transcribe()
print(trans)
oscClient.send_message("/chatbox/input", [trans, True, True])
oscClient.send_message("/chatbox/typing", False)


