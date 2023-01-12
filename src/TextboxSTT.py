import os
import sys
import json
import logging
from UI import UI
from settings_UI import settings_ui
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

class TextboxSTT:
    def __init__(self, config):
        self.config = config
        self.osc_client = None
        self.kat = None
        self.textbox = None
        self.model = "base"
        self.lang = "english"
        self.r = None
        self.use_cpu = True
        self.ovr_initialized = False
        self.application = None
        self.action_set_handle = None
        self.buttonactionhandle = None

        self.curr_time = 0.0
        self.pressed = False
        self.holding = False
        self.held = False
        self.thread_process = threading.Thread(target=self.process_stt)

        self.config_ui = None
        self.initialize()

    def initialize(self):
        self.config_ui = None
        self.osc_client = udp_client.SimpleUDPClient(self.config["osc_ip"], int(self.config["osc_port"]))
        self.textbox = bool(self.config["use_textbox"])
        if self.config["use_kat"]:
            self.kat =  KatOsc(self.osc_client, self.config["osc_ip"], self.config["osc_server_port"], True)

        self.model = self.config["model"].lower()
        self.lang = self.config["language"].lower()
        if self.lang == "":
            self.lang = None
        elif self.model != "large" and self.lang == "english" and ".en" not in self.model:
            self.model = self.model + ".en"
        ui.set_status_label(f"LOADING \"{self.model}\" MODEL", "orange")
        # Temporarily output stderr to text label for download progress.
        sys.stderr.write = ui.loading_status
        # Load Whisper model
        self.model = whisper.load_model(self.model, download_root=get_absolute_path("whisper_cache/"), in_memory=True)
        self.use_cpu = True if str(self.model.device) == "cpu" else False

        sys.stderr = StreamToLogger(log, logging.ERROR, LOGFILE)

        # load the speech recognizer and set the initial energy threshold and pause threshold
        self.r = sr.Recognizer()
        self.r.dynamic_energy_threshold = bool(self.config["dynamic_energy_threshold"])
        self.r.energy_threshold = int(self.config["energy_threshold"])
        self.r.pause_threshold = float(self.config["pause_threshold"])

        # Initialize OpenVR
        ui.set_status_label("INITIALIZING OVR", "orange")
        self.ovr_initialized = False
        try:
            self.application = openvr.init(openvr.VRApplication_Utility)
            action_path = get_absolute_path("bindings/textboxstt_actions.json")
            appmanifest_path = get_absolute_path("app.vrmanifest")
            openvr.VRApplications().addApplicationManifest(appmanifest_path)
            openvr.VRInput().setActionManifestPath(action_path)
            
            self.action_set_handle = openvr.VRInput().getActionSetHandle(ACTIONSETHANDLE)
            self.buttonactionhandle = openvr.VRInput().getActionHandle(STTLISTENHANDLE)
            self.ovr_initialized = True
            ui.set_status_label("INITIALZIED", "green")
        except Exception:
            self.ovr_initialized = False
            ui.set_status_label("COULDNT INITIALIZE OVR, CONTINUING DESKTOP ONLY", "red")

        ui.set_conf_label(self.config["osc_ip"], self.config["osc_port"], self.ovr_initialized, self.use_cpu)
        ui.set_status_label("INITIALZIED - WAITING FOR INPUT", "green")


    def play_sound(self, filename):
        """Plays a wave file."""
        filename = f"resources/{filename}.wav"
        winsound.PlaySound(get_absolute_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)


    def listen(self):
        device_index = None
        if self.config["microphone_index"]:
            device_index = int(self.config["microphone_index"])
        with sr.Microphone(device_index, sample_rate=16000) as source:
            try:
                audio = self.r.listen(source, timeout=float(self.config["timeout_time"]))
            except sr.WaitTimeoutError:
                return None

            return torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)


    def transcribe(self, torch_audio, language):
        use_gpu = not self.use_cpu
        torch_audio = whisper.pad_or_trim(torch_audio)
        options = whisper.DecodingOptions(language=language, fp16=use_gpu, without_timestamps=True)
        mel = whisper.log_mel_spectrogram(torch_audio).to(self.model.device)
        t = CustomThread(target=whisper.decode, args=[self.model, mel, options])
        t.start()

        timeout = float(self.config["max_transcribe_time"])
        if timeout == 0.0:
            timeout = None
        result = t.join(timeout)

        if result:
            result = result.text.strip()
            # Filter by banned words
            for word in self.config["banned_words"]:
                tmp = re.compile(word, re.IGNORECASE)
                result = tmp.sub("", result)
            result = re.sub(' +', ' ', result)

        return result


    def clear_chatbox(self):
        ui.set_status_label("CLEARING OSC TEXTBOX", "#e0ffff")
        if self.textbox:
            self.osc_client.send_message(VRC_INPUT_PARAM, ["", True, False])
            self.osc_client.send_message(VRC_TYPING_PARAM, False)
        if self.kat:
            self.kat.clear()
            self.kat.hide()
        ui.set_status_label("CLEARED - WAITING FOR INPUT", "#00008b")
        ui.set_text_label("- No Text -")


    def set_typing_indicator(self, b: bool):
        if self.textbox:
            self.osc_client.send_message(VRC_TYPING_PARAM, b)
        if self.kat:
            self.osc_client.send_message(AV_LISTENING_PARAM, b)


    def populate_chatbox(self, text):
        text = text[:VRC_INPUT_CHARLIMIT]
        ui.set_text_label(text)
        print("Transcribed: " + text)
        ui.set_status_label("POPULATING TEXTBOX", "#ff8800")
        if self.textbox:
            self.osc_client.send_message(VRC_INPUT_PARAM, [text, True, True])
        if self.kat:
            self.kat.set_text(text[:KAT_CHARLIMIT])
        self.set_typing_indicator(False)
        ui.set_status_label("WAITING FOR INPUT", "#00008b")


    def get_ovraction_bstate(self):
        event = openvr.VREvent_t()
        has_events = True
        while has_events:
            has_events = self.application.pollNextEvent(event)
        _actionsets = (openvr.VRActiveActionSet_t * 1)()
        _actionset = _actionsets[0]
        _actionset.ulActionSet = self.action_set_handle
        openvr.VRInput().updateActionState(_actionsets)
        return bool(openvr.VRInput().getDigitalActionData(self.buttonactionhandle, openvr.k_ulInvalidInputValueHandle).bState)


    def get_trigger_state(self):
        if self.ovr_initialized and self.get_ovraction_bstate():
            return True
        else:
            return keyboard.is_pressed(self.config["hotkey"])


    def process_stt(self):
        self.set_typing_indicator(True)
        ui.set_status_label("LISTENING", "#FF00FF")
        self.play_sound("listen")
        torch_audio = self.listen()
        if torch_audio is None:
            ui.set_status_label("TIMEOUT - WAITING FOR INPUT", "orange")
            self.play_sound("timeout")
            self.set_typing_indicator(False)
        else:
            self.play_sound("donelisten")
            self.set_typing_indicator(True)
            print(torch_audio)
            ui.set_status_label("TRANSCRIBING", "orange")

            if not self.pressed:
                trans = self.transcribe(torch_audio, self.lang)
                if self.pressed:
                    ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                    self.play_sound("timeout")
                elif trans:
                    self.populate_chatbox(trans)
                    self.play_sound("finished")
                else:
                    ui.set_status_label("ERROR TRANSCRIBING - WAITING FOR INPUT", "red")
                    self.play_sound("timeout")
            else:
                ui.set_status_label("CANCELED - WAITING FOR INPUT", "orange")
                self.play_sound("timeout")

        self.set_typing_indicator(False)


    def handle_input(self):
        self.pressed = self.get_trigger_state()

        if self.thread_process.is_alive():
            return
        elif self.pressed and not self.holding and not self.held:
            self.holding = True
            self.curr_time = time.time()
        elif self.pressed and self.holding and not self.held:
            self.holding = True
            if time.time() - self.curr_time > float(self.config["hold_time"]):
                self.clear_chatbox()
                self.play_sound("clear")
                self.held = True
                self.holding = False
        elif not self.pressed and self.holding and not self.held:
            self.held = True
            self.holding = False
            thread_process = threading.Thread(target=self.process_stt)
            thread_process.start()
        elif not self.pressed and self.held:
            self.held = False
            self.holding = False


    def entrybox_enter_event(self, text):
        if text:
            self.populate_chatbox(text)
            self.play_sound("finished")
            ui.clear_textfield()
        else:
            self.clear_chatbox()
            self.play_sound("clear")
    

    def on_closing(self):
        self.kat.stop()
        ui.tkui.destroy()


    def settings_closed(self):
        self.config_ui.on_closing()
        self.kat.stop()
        self.initialize()


    def open_settings(self):
        self.config_ui = settings_ui(self.config)
        self.config_ui.tkui.protocol("WM_DELETE_WINDOW", self.settings_closed)
        self.config_ui.run()


config = json.load(open(get_absolute_path('config.json')))
ui = UI(VERSION, config)
app = TextboxSTT(config)

ui.tkui.protocol("WM_DELETE_WINDOW", app.on_closing)
ui.textfield.bind("<Return>", (lambda event: app.entrybox_enter_event(ui.textfield.get())))
ui.textfield.bind("<Key>", (lambda event: app.set_typing_indicator(True)))
ui.btn_settings.bind("<ButtonPress>", (lambda event: app.open_settings()))
ui.create_loop(50, app.handle_input)
ui.tkui.mainloop()
