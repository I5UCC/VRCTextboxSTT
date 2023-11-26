import tkinter as tk
import json
import pyaudio
import keyboard
import glob
import shutil
import os
import torch
from helper import get_best_compute_type, get_absolute_path
from ctranslate2 import get_supported_compute_types
from config import config_struct, LANGUAGE_TO_KEY, WHISPER_MODELS
from multiprocessing import cpu_count
import logging
import traceback

log = logging.getLogger(__name__)

class MainWindow(object):
    def __init__(self, script_path, x=None, y=None):

        self.version = "RELEASE"
        try:
            self.version = open(get_absolute_path("VERSION", script_path)).readline().rstrip()
        except Exception:
            pass

        self.icon_path = get_absolute_path("resources/icon.ico", script_path)

        log.info(f"VRCTextboxSTT {self.version} by I5UCC")

        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        if x and y:
            self.tkui.geometry(f"+{x}+{y}")
            self.coodinates = (x, y)
        else:
            self.coodinates = self.get_coordinates()
        self.tkui.minsize(810, 380)
        self.tkui.maxsize(810, 380)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT")
        self.tkui.iconbitmap(self.icon_path)

        self.text_lbl = tk.Label(self.tkui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 27))
        self.text_lbl.place(relx=0.5, rely=0.45, anchor="center")

        self.conf_lbl = tk.Label(self.tkui, text=f"Loading...")
        self.conf_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.conf_lbl.place(relx=0.01, rely=0.935, anchor="w")

        self.time_lbl = tk.Label(self.tkui, text=f"0.000s")
        self.time_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.time_lbl.place(relx=0.075, rely=0.78, anchor="e")

        self.ver_lbl = tk.Label(self.tkui, text=f"VRCTextboxSTT {self.version} by I5UCC")
        self.ver_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.ver_lbl.place(relx=0.99, rely=0.05, anchor="e")

        self.status_lbl = tk.Label(self.tkui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.tkui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=(self.FONT, 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.btn_copy = tk.Button(self.tkui, text="📋")
        self.btn_copy.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=6, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_copy.place(relx=0.99, rely=0.76, anchor="e")

        self.btn_settings = tk.Button(self.tkui, text="⚙")
        self.btn_settings.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=6, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled")
        self.btn_settings.place(relx=0.99, rely=0.94, anchor="e")

        self.btn_refresh = tk.Button(self.tkui, text="⭯")
        self.btn_refresh.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=6, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled")
        self.btn_refresh.place(relx=0.915, rely=0.94, anchor="e")

        self.textfield = tk.Entry(self.tkui)
        self.textfield.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=25, highlightthickness=0, insertbackground="#666666")
        self.textfield.place(relx=0.5, rely=0.845, anchor="center", width=792, height=25)

        self.update()

    def show_update_button(self, text):
        self.btn_update = tk.Button(self.tkui, text=text)
        self.btn_update.configure(bg="#333333", fg="white", font=(self.FONT, 10), anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_update.place(relx=0.99, rely=0.14, anchor="e")

    def run_loop(self):
        self.tkui.mainloop()

    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def create_loop(self, intervall, func):
        func()
        self.tkui.after(intervall, self.create_loop, *[intervall, func])

    def set_status_label(self, text, color="orange"):
        self.status_lbl.configure(text=text)
        self.color_lbl.configure(bg=color)
        self.update()
        log.info(text)

    def set_text_label(self, text):
        self.text_lbl.configure(text=text)
        self.update()

    def loading_status(self, s: str):
        try:
            self.set_text_label(f"Downloading Model:{s[s.rindex('|')+1:]}")
            self.update()
        except Exception:
            pass

    def set_conf_label(self, ip, port, server_port, http_port, ovr_initialized, device, model, compute_type, cpu_threads, num_workers, vad):
        _cpu_str = f", CPU Threads: {cpu_threads}" if device.lower() == "cpu" else ""
        self.conf_lbl.configure(justify="left", text=f"OSC: {ip}#{port}:{server_port}:{http_port}, OVR: {'Connected' if ovr_initialized else 'Disconnected'}, Device: {device}{_cpu_str}\nModel: {model}, Compute Type: {compute_type}, Workers: {num_workers}, VAD: {vad}")
        self.update()

    def set_time_label(self, time):
        self.time_lbl.configure(text=f"{time:0.3f}s")
        self.update()

    def clear_textfield(self):
        self.textfield.delete(0, tk.END)
        self.update()

    def on_closing(self):
        self.tkui.destroy()

    def set_button_enabled(self, state=False):
        if state:
            self.btn_settings.configure(state="normal")
            self.btn_refresh.configure(state="normal")
        else:
            self.btn_settings.configure(state="disabled")
            self.btn_refresh.configure(state="disabled")

    def get_coordinates(self):
        return (self.tkui.winfo_x(), self.tkui.winfo_y())


class SettingsWindow:
    def __init__(self, conf: config_struct, config_path, script_path, get_coodinates, restart_func):
        self.restart_func = restart_func
        self.languages = ["Auto Detect"] + list(LANGUAGE_TO_KEY.keys())
        self.icon_path = get_absolute_path("resources/icon.ico", script_path)
        
        self.config = conf
        self.config_path = config_path
        self.FONT = "Cascadia Code"
        PADX_R = '0'
        PADX_L = '10'
        PADY = '4'
        self.yn_options = ["ON", "OFF"]
        self.whisper_models = ["base"]
        self.whisper_models = [x for x in self.whisper_models if ".en" not in x]
        self.tooltip_window = None

        self.tkui = tk.Tk()
        coordinates = get_coodinates()
        self.tkui.geometry(f"+{coordinates[0] - 22}+{coordinates[1] - 22}")
        self.tkui.minsize(920, 610)
        self.tkui.maxsize(920, 610)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Settings")
        self.tkui.iconbitmap(self.icon_path)

        self.devices_list = []
        self.value_device = tk.StringVar(self.tkui)

        if torch.cuda.is_available():
            for i in range(0, torch.cuda.device_count()):
                self.devices_list.append((i, torch.cuda.get_device_name(i)))
            if self.config.whisper.device.type != "cpu":
                _index = int(self.config.whisper.device.index)
                self.value_device.set(self.devices_list[_index])

        if self.config.whisper.device.type == "cpu" or not torch.cuda.is_available():
            self.value_device.set("CPU")

        self.devices_list.append("CPU")

        self.label_device = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Device *', font=(self.FONT, 12))
        self.label_device.grid(row=0, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.opt_device = tk.OptionMenu(self.tkui, self.value_device, *self.devices_list)
        self.opt_device.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_device.grid(row=0, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_device.bind("<Enter>", (lambda event: self.show_tooltip("Set the Device to use for transcription. (Requires Restart)")))
        self.label_device.bind("<Leave>", self.hide_tooltip)
        self.opt_device.bind("<Enter>", (lambda event: self.show_tooltip("Set the Device to use for transcription. (Requires Restart)")))
        self.opt_device.bind("<Leave>", self.hide_tooltip)
        self.button_device_overlay = tk.Button(self.tkui, text=" ⚙ ", command=self.open_device_window)
        self.button_device_overlay.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_device_overlay.grid(row=0, column=2, padx=2, pady=7, sticky='ws')
        self.button_device_overlay.bind("<Enter>", (lambda event: self.show_tooltip("Edit Device Settings")))
        self.button_device_overlay.bind("<Leave>", self.hide_tooltip)

        self.label_osc_ip = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC IP *', font=(self.FONT, 12))
        self.label_osc_ip.grid(row=1, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_ip.bind("<Enter>", (lambda event: self.show_tooltip("IP to send the OSC information to.")))
        self.label_osc_ip.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_ip = tk.Entry(self.tkui)
        self.entry_osc_ip.insert(0, self.config.osc.ip)
        self.entry_osc_ip.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_ip.grid(row=1, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_ip.bind("<Enter>", (lambda event: self.show_tooltip("IP to send the OSC information to.")))
        self.entry_osc_ip.bind("<Leave>", self.hide_tooltip)

        self.label_osc_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Port *', font=(self.FONT, 12))
        self.label_osc_port.grid(row=2, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to send the OSC information to.")))
        self.label_osc_port.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_port = tk.Entry(self.tkui)
        self.entry_osc_port.insert(0, self.config.osc.client_port)
        self.entry_osc_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_port.grid(row=2, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to send the OSC information to.")))
        self.entry_osc_port.bind("<Leave>", self.hide_tooltip)

        self.label_osc_server_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Server Port *', font=(self.FONT, 12))
        self.label_osc_server_port.grid(row=3, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_osc_server_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to get the OSC information from.\nUsed to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar.\nKeep at 9001 to use the default port.\nSet to 0 to auto-detect the port with OSC-Query.\nSet to -1 to disable receiving OSC information entirely.")))
        self.label_osc_server_port.bind("<Leave>", self.hide_tooltip)
        self.entry_osc_server_port = tk.Entry(self.tkui)
        self.entry_osc_server_port.insert(0, self.config.osc.server_port)
        self.entry_osc_server_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23, disabledbackground="#444444")
        self.entry_osc_server_port.grid(row=3, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_osc_server_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to get the OSC information from.\nUsed to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar.\nKeep at 9001 to use the default port.\nSet to 0 to auto-detect the port with OSC-Query.\nSet to -1 to disable receiving OSC information entirely.")))
        self.entry_osc_server_port.bind("<Leave>", self.hide_tooltip)

        self.label_model = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Model *', font=(self.FONT, 12))
        self.label_model.grid(row=4, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_model.bind("<Enter>", (lambda event: self.show_tooltip("What model of whisper to use. \nI'd recommend not going over 'tiny,base,small'\n as it will significantly impact the transcription time.")))
        self.label_model.bind("<Leave>", self.hide_tooltip)
        self.value_model = tk.StringVar(self.tkui)
        self.value_model.set(self.config.whisper.model)
        self.value_model.trace("w", self.model_changed)
        self.models = []
        for key in WHISPER_MODELS:
            if ".en" not in key:
                self.models.append(key)
        if self.config.whisper.custom_models:
            self.models = self.models + self.config.whisper.custom_models
        self.models.append("custom")
        self.entry_model = tk.Entry(self.tkui)
        self.entry_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_model.bind("<Return>", (lambda event: self.entry_model_enter_event(self.entry_model.get())))
        self.entry_model.bind("<Enter>", (lambda event: self.show_tooltip("Custom Model to use, should be the huggingface path. i.e. openai/whisper-tiny\nPress enter on the empty field to switch back to selecting a model.")))
        self.entry_model.bind("<Leave>", self.hide_tooltip)
        self.opt_model = tk.OptionMenu(self.tkui, self.value_model, *self.models)
        self.opt_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_model.grid(row=4, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_model.bind("<Enter>", (lambda event: self.show_tooltip("What model of whisper to use. \nI'd recommend not going over 'tiny,base,small'\n as it will significantly impact the transcription time.")))
        self.opt_model.bind("<Leave>", self.hide_tooltip)

        self.label_vad = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Voice Activity Detection', font=(self.FONT, 12))
        self.label_vad.grid(row=5, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_vad.bind("<Enter>", (lambda event: self.show_tooltip("Applys voice activity detection to the audio stream. \nThis will remove any silence or noise from the audio stream, \nwhich can make the transcription faster. \nHowever, it will also remove any pauses in the audio stream.")))
        self.label_vad.bind("<Leave>", self.hide_tooltip)
        self.value_vad = tk.StringVar(self.tkui)
        self.value_vad.set("ON" if self.config.vad.enabled else "OFF")
        self.opt_vad = tk.OptionMenu(self.tkui, self.value_vad, *self.yn_options)
        self.opt_vad.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_vad.grid(row=5, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_vad.bind("<Enter>", (lambda event: self.show_tooltip("Applys voice activity detection to the audio stream. \nThis will remove any silence or noise from the audio stream, \nwhich can make the transcription faster. \nHowever, it will also remove any pauses in the audio stream.")))
        self.opt_vad.bind("<Leave>", self.hide_tooltip)
        self.button_vad_settings = tk.Button(self.tkui, text=" ⚙ ", command=self.open_vad_window)
        self.button_vad_settings.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_vad_settings.grid(row=5, column=2, padx=2, pady=7, sticky='ws')
        self.button_vad_settings.bind("<Enter>", (lambda event: self.show_tooltip("Edit Device Settings")))
        self.button_vad_settings.bind("<Leave>", self.hide_tooltip)

        self.label_language = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Language *', font=(self.FONT, 12))
        self.label_language.grid(row=6, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_language.bind("<Enter>", (lambda event: self.show_tooltip("Language to use, 'english' will be faster then other languages. \nLeaving it empty will let the program decide what language you are speaking.")))
        self.label_language.bind("<Leave>", self.hide_tooltip)
        self.value_language = tk.StringVar(self.tkui)
        self.value_language.set("Auto Detect" if not self.config.whisper.language else self.config.whisper.language)
        self.opt_language = tk.OptionMenu(self.tkui, self.value_language, *self.languages)
        self.opt_language.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_language.grid(row=6, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_language.bind("<Enter>", (lambda event: self.show_tooltip("Language to use, 'english' will be faster then other languages. \nLeaving it empty will let the program decide what language you are speaking.")))
        self.opt_language.bind("<Leave>", self.hide_tooltip)

        self.label_translate = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Translate to *', font=(self.FONT, 12))
        self.label_translate.bind("<Enter>", (lambda event: self.show_tooltip("Translate the transcription to another language.")))
        self.label_translate.bind("<Leave>", self.hide_tooltip)
        self.label_translate.grid(row=7, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_translate = tk.StringVar(self.tkui)
        self.value_translate.set("OFF" if not self.config.translator.language else self.config.translator.language)
        self.languages[0] = "OFF"
        self.opt_translate = tk.OptionMenu(self.tkui, self.value_translate, *self.languages)
        self.opt_translate.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_translate.grid(row=7, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_translate.bind("<Enter>", (lambda event: self.show_tooltip("Translate the transcription to another language.")))
        self.opt_translate.bind("<Leave>", self.hide_tooltip)
        self.button_translate_settings = tk.Button(self.tkui, text=" ⚙ ", command=self.open_translate_window)
        self.button_translate_settings.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_translate_settings.grid(row=7, column=2, padx=2, pady=7, sticky='ws')
        self.button_translate_settings.bind("<Enter>", (lambda event: self.show_tooltip("Edit Device Settings")))
        self.button_translate_settings.bind("<Leave>", self.hide_tooltip)

        self.label_autocorrect = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Auto-Correct', font=(self.FONT, 12))
        self.label_autocorrect.bind("<Enter>", (lambda event: self.show_tooltip("Auto-Correct text manually written in the text to text box.")))
        self.label_autocorrect.bind("<Leave>", self.hide_tooltip)
        self.label_autocorrect.grid(row=8, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_autocorrect = tk.StringVar(self.tkui)
        self.value_autocorrect.set("OFF" if not self.config.autocorrect.language else self.config.autocorrect.language)
        self.autocorrect_languages = ["OFF", "english", "polish", "turkish", "russian", "ukrainian", "czech", "portuguese", "greek", "italian", "vietnamese", "french", "spanish"]
        self.opt_autocorrect = tk.OptionMenu(self.tkui, self.value_autocorrect, *self.autocorrect_languages)
        self.opt_autocorrect.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_autocorrect.grid(row=8, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_autocorrect.bind("<Enter>", (lambda event: self.show_tooltip("Auto-Correct text manually written in the text to text box.")))
        self.opt_autocorrect.bind("<Leave>", self.hide_tooltip)

        self.label_hotkey = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hotkey', font=(self.FONT, 12))
        self.label_hotkey.grid(row=9, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_hotkey.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nClick on the button and press the button you want to use.")))
        self.label_hotkey.bind("<Leave>", self.hide_tooltip)
        self.set_key = self.config.hotkey
        self.button_hotkey = tk.Button(self.tkui, text=self.config.hotkey, command=self.button_hotkey_pressed)
        self.button_hotkey.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=23, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_hotkey.grid(row=9, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.button_hotkey.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nClick on the button and press the button you want to use.")))
        self.button_hotkey.bind("<Leave>", self.hide_tooltip)

        self.label_mode = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Transcription Mode', font=(self.FONT, 12))
        self.label_mode.grid(row=10, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_mode.bind("<Enter>", (lambda event: self.show_tooltip("If set to 'realtime' it will show interim results while you are talking until you are done talking.\nIf set to 'once' it will only listen once and then stop listening, like it used to be.")))
        self.label_mode.bind("<Leave>", self.hide_tooltip)
        self.value_mode = tk.StringVar(self.tkui)
        self.options_mode = ["once", "once_continuous", "realtime"]
        self.value_mode.set(self.options_mode[self.config.mode])
        self.value_mode.trace("w", self.mode_changed)
        self.opt_mode = tk.OptionMenu(self.tkui, self.value_mode, *self.options_mode)
        self.opt_mode.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mode.grid(row=10, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_mode.bind("<Enter>", (lambda event: self.show_tooltip("If set to 'realtime' it will show interim results while you are talking until you are done talking.\nIf set to 'once' it will only listen once and then stop listening, like it used to be.")))
        self.opt_mode.bind("<Leave>", self.hide_tooltip)
        self.value_mode.trace_add("write", (lambda *args: self.changed()))

        self.label_det = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Dynamic Energy Threshold', font=(self.FONT, 12))
        self.label_det.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.label_det.bind("<Leave>", self.hide_tooltip)
        self.label_det.grid(row=11, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_det = tk.StringVar(self.tkui)
        self.value_det.set("ON" if bool(self.config.listener.dynamic_energy_threshold) else "OFF")
        self.opt_det = tk.OptionMenu(self.tkui, self.value_det, *self.yn_options)
        self.opt_det.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_det.grid(row=11, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_det.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will realtimely try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.opt_det.bind("<Leave>", self.hide_tooltip)

        self.label_energy_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Energy Threshold', font=(self.FONT, 12))
        self.label_energy_threshold.grid(row=12, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_energy_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.label_energy_threshold.bind("<Leave>", self.hide_tooltip)
        self.entry_energy_threshold = tk.Entry(self.tkui)
        self.entry_energy_threshold.insert(0, self.config.listener.energy_threshold)
        self.entry_energy_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_energy_threshold.grid(row=12, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_energy_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.entry_energy_threshold.bind("<Leave>", self.hide_tooltip)
        self.button_refresh = tk.Button(self.tkui, text=" ⭯ ")
        self.button_refresh.configure(bg="#333333", fg="white", highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_refresh.grid(row=12, column=2, padx=2, pady=3, sticky='ws')
        self.button_refresh.bind("<Enter>", (lambda event: self.show_tooltip("Manually refreshes the energy threshold value. \n Be silent for 5 Seconds after pressing this button. \n The Textfield is going to be populated with the new value.")))
        self.button_refresh.bind("<Leave>", self.hide_tooltip)

        self.label_clipboard_mode = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Copy Clipboard Mode', font=(self.FONT, 12))
        self.label_clipboard_mode.grid(row=13, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.label_clipboard_mode.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.label_clipboard_mode.bind("<Leave>", self.hide_tooltip)
        self.options_clipboard_mode = ["Manual", "Always"]
        self.value_clipboard_mode = tk.StringVar(self.tkui)
        self.value_clipboard_mode.set("Always" if self.config.always_clipboard else "Manual")
        self.opt_clipboard_mode = tk.OptionMenu(self.tkui, self.value_clipboard_mode, *self.options_clipboard_mode)
        self.opt_clipboard_mode.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_clipboard_mode.grid(row=13, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_clipboard_mode.bind("<Enter>", (lambda event: self.show_tooltip("Writes the transcription to the clipboard.\nIf set to 'Manual' you can press the '📋' button to copy the text to the clipboard.\nIf set to 'Always' it will automatically copy the text to the clipboard.")))
        self.opt_clipboard_mode.bind("<Leave>", self.hide_tooltip)

        self.label_pause_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Pause Threshold', font=(self.FONT, 12))
        self.label_pause_threshold.grid(row=0, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_pause_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Amount of seconds to wait when current energy is under the 'energy_threshold'.\n Only used in 'realtime' and 'once_continuos' mode.")))
        self.label_pause_threshold.bind("<Leave>", self.hide_tooltip)
        self.entry_pause_threshold = tk.Entry(self.tkui)
        self.entry_pause_threshold.insert(0, self.config.listener.pause_threshold)
        self.entry_pause_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_pause_threshold.grid(row=0, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_pause_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Amount of seconds to wait when current energy is under the 'energy_threshold'.\n Only used in 'realtime' and 'once_continuos' mode.")))
        self.entry_pause_threshold.bind("<Leave>", self.hide_tooltip)

        self.label_text_timeout_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Text Timeout Time', font=(self.FONT, 12))
        self.label_text_timeout_time.grid(row=1, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_text_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait until the text is cleared.\n0 = Never Clear")))
        self.label_text_timeout_time.bind("<Leave>", self.hide_tooltip)
        self.entry_text_timeout_time = tk.Entry(self.tkui)
        self.entry_text_timeout_time.insert(0, self.config.text_timeout)
        self.entry_text_timeout_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_text_timeout_time.grid(row=1, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_text_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait until the text is cleared.\n0 = Never Clear")))
        self.entry_text_timeout_time.bind("<Leave>", self.hide_tooltip)

        self.label_timeout_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Listen Timeout Time', font=(self.FONT, 12))
        self.label_timeout_time.grid(row=2, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait for the user to speak before timeout.")))
        self.label_timeout_time.bind("<Leave>", self.hide_tooltip)
        self.entry_timeout_time = tk.Entry(self.tkui)
        self.entry_timeout_time.insert(0, self.config.listener.timeout_time)
        self.entry_timeout_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_timeout_time.grid(row=2, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait for the user to speak before timeout.")))
        self.entry_timeout_time.bind("<Leave>", self.hide_tooltip)

        self.label_hold_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hold Time', font=(self.FONT, 12))
        self.label_hold_time.grid(row=3, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_hold_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to hold the button to clear the Textbox.")))
        self.label_hold_time.bind("<Leave>", self.hide_tooltip)
        self.entry_hold_time = tk.Entry(self.tkui)
        self.entry_hold_time.insert(0, self.config.listener.hold_time)
        self.entry_hold_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_hold_time.grid(row=3, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_hold_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to hold the button to clear the Textbox.")))
        self.entry_hold_time.bind("<Leave>", self.hide_tooltip)

        self.label_phrase_time_limit = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Phrase time limit', font=(self.FONT, 12))
        self.label_phrase_time_limit.grid(row=4, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_phrase_time_limit.bind("<Enter>", (lambda event: self.show_tooltip("The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached")))
        self.label_phrase_time_limit.bind("<Leave>", self.hide_tooltip)
        self.entry_phrase_time_limit = tk.Entry(self.tkui)
        self.entry_phrase_time_limit.insert(0, self.config.listener.phrase_time_limit)
        self.entry_phrase_time_limit.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_phrase_time_limit.grid(row=4, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.entry_phrase_time_limit.bind("<Enter>", (lambda event: self.show_tooltip("The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached")))
        self.entry_phrase_time_limit.bind("<Leave>", self.hide_tooltip)

        self.label_audio_feedback = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Enable Audio Feedback', font=(self.FONT, 12))
        self.label_audio_feedback.grid(row=5, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_audio_feedback.bind("<Enter>", (lambda event: self.show_tooltip("If you want enable Audio Feedback")))
        self.label_audio_feedback.bind("<Leave>", self.hide_tooltip)
        self.value_audio_feedback = tk.StringVar(self.tkui)
        self.value_audio_feedback.set("ON" if bool(self.config.audio_feedback.enabled) else "OFF")
        self.opt_audio_feedback = tk.OptionMenu(self.tkui, self.value_audio_feedback, *self.yn_options)
        self.opt_audio_feedback.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_audio_feedback.grid(row=5, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_audio_feedback.bind("<Enter>", (lambda event: self.show_tooltip("If you want enable Audio Feedback")))
        self.opt_audio_feedback.bind("<Leave>", self.hide_tooltip)
        self.button_audio_feedback = tk.Button(self.tkui, text=" ⚙ ", command=self.open_audio_window)
        self.button_audio_feedback.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_audio_feedback.grid(row=5, column=6, padx=2, pady=7, sticky='ws')
        self.button_audio_feedback.bind("<Enter>", (lambda event: self.show_tooltip("Edit OBS Source Settings (Requires Restart)")))
        self.button_audio_feedback.bind("<Leave>", self.hide_tooltip)

        self.label_enable_overlay = tk.Label(master=self.tkui, bg="#333333", fg="white", text='SteamVR Overlay', font=(self.FONT, 12))
        self.label_enable_overlay.grid(row=6, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_enable_overlay.bind("<Enter>", (lambda event: self.show_tooltip("A SteamVR Overlay that shows the transcription right in front of you.")))
        self.label_enable_overlay.bind("<Leave>", self.hide_tooltip)
        self.value_enable_overlay = tk.StringVar(self.tkui)
        self.value_enable_overlay.set("ON" if bool(self.config.overlay.enabled) else "OFF")
        self.opt_enable_overlay = tk.OptionMenu(self.tkui, self.value_enable_overlay, *self.yn_options)
        self.opt_enable_overlay.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_enable_overlay.grid(row=6, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_enable_overlay.bind("<Enter>", (lambda event: self.show_tooltip("A SteamVR Overlay that shows the transcription right in front of you.")))
        self.opt_enable_overlay.bind("<Leave>", self.hide_tooltip)
        self.value_enable_overlay.trace_add("write", (lambda *args: self.changed()))
        self.button_settings_overlay = tk.Button(self.tkui, text=" ⚙ ", command=self.open_overlay_window)
        self.button_settings_overlay.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_settings_overlay.grid(row=6, column=6, padx=2, pady=7, sticky='ws')
        self.button_settings_overlay.bind("<Enter>", (lambda event: self.show_tooltip("Edit Overlay Settings")))
        self.button_settings_overlay.bind("<Leave>", self.hide_tooltip)

        self.label_obs_source = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Enable OBS Source *', font=(self.FONT, 12))
        self.label_obs_source.grid(row=7, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.label_obs_source.bind("<Leave>", self.hide_tooltip)
        self.value_obs_source = tk.StringVar(self.tkui)
        self.value_obs_source.set("ON" if bool(self.config.obs.enabled) else "OFF")
        self.opt_obs_source = tk.OptionMenu(self.tkui, self.value_obs_source, *self.yn_options)
        self.opt_obs_source.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_obs_source.grid(row=7, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.opt_obs_source.bind("<Leave>", self.hide_tooltip)
        self.value_obs_source.trace_add("write", (lambda *args: self.changed()))
        self.button_obs_source = tk.Button(self.tkui, text=" ⚙ ", command=self.open_obs_window)
        self.button_obs_source.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_obs_source.grid(row=7, column=6, padx=2, pady=7, sticky='ws')
        self.button_obs_source.bind("<Enter>", (lambda event: self.show_tooltip("Edit OBS Source Settings (Requires Restart)")))
        self.button_obs_source.bind("<Leave>", self.hide_tooltip)
        
        self.label_websocket = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Enable Websocket *', font=(self.FONT, 12))
        self.label_websocket.grid(row=8, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_websocket.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.label_websocket.bind("<Leave>", self.hide_tooltip)
        self.value_websocket = tk.StringVar(self.tkui)
        self.value_websocket.set("ON" if bool(self.config.websocket.enabled) else "OFF")
        self.opt_websocket = tk.OptionMenu(self.tkui, self.value_websocket, *self.yn_options)
        self.opt_websocket.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_websocket.grid(row=8, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_websocket.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use the OBS Browser Source (Requires Restart)")))
        self.opt_websocket.bind("<Leave>", self.hide_tooltip)
        self.button_websocket = tk.Button(self.tkui, text=" ⚙ ", command=self.open_websocket_window)
        self.button_websocket.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_websocket.grid(row=8, column=6, padx=2, pady=7, sticky='ws')
        self.button_websocket.bind("<Enter>", (lambda event: self.show_tooltip("Edit Websocket Settings (Requires Restart)")))
        self.button_websocket.bind("<Leave>", self.hide_tooltip)

        self.label_mic = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Microphone', font=(self.FONT, 12))
        self.label_mic.grid(row=9, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_mic.bind("<Enter>", (lambda event: self.show_tooltip("What microphone to use. 'Default' will use your systems default microphone.")))
        self.label_mic.bind("<Leave>", self.hide_tooltip)
        self.option_index = 0 if self.config.listener.microphone_index is None else int(self.config.listener.microphone_index) + 1
        self.options_mic = self.get_sound_devices()
        self.value_mic = tk.StringVar(self.tkui)
        try:
            self.value_mic.set(self.options_mic[self.option_index])
        except IndexError:
            self.value_mic.set("Default")
        self.opt_mic = tk.OptionMenu(self.tkui, self.value_mic, *self.options_mic)
        self.opt_mic.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mic.grid(row=9, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_mic.bind("<Enter>", (lambda event: self.show_tooltip("What microphone to use. 'Default' will use your systems default microphone.")))
        self.opt_mic.bind("<Leave>", self.hide_tooltip)

        self.label_word_replacements = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Word Replacement', font=(self.FONT, 12))
        self.label_word_replacements.grid(row=10, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_word_replacements.bind("<Enter>", (lambda event: self.show_tooltip("If you want to enable Word replacements.")))
        self.label_word_replacements.bind("<Leave>", self.hide_tooltip)
        self.value_word_replacements = tk.StringVar(self.tkui)
        self.value_word_replacements.set("ON" if bool(self.config.wordreplacement.enabled) else "OFF")
        self.opt_enable_replacement = tk.OptionMenu(self.tkui, self.value_word_replacements, *self.yn_options)
        self.opt_enable_replacement.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_enable_replacement.grid(row=10, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_enable_replacement.bind("<Enter>", (lambda event: self.show_tooltip("If you want to enable Word replacements.")))
        self.opt_enable_replacement.bind("<Leave>", self.hide_tooltip)
        self.button_word_replacements = tk.Button(self.tkui, text=" ⚙ ", command=self.open_replacement_window)
        self.button_word_replacements.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_word_replacements.grid(row=10, column=6, padx=2, pady=7, sticky='ws')
        self.button_word_replacements.bind("<Enter>", (lambda event: self.show_tooltip("Edit Word replacements.")))
        self.button_word_replacements.bind("<Leave>", self.hide_tooltip)

        self.label_use_textbox = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Textbox', font=(self.FONT, 12))
        self.label_use_textbox.grid(row=11, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_textbox.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.label_use_textbox.bind("<Leave>", self.hide_tooltip)
        self.value_use_textbox = tk.StringVar(self.tkui)
        self.value_use_textbox.set("ON" if bool(self.config.osc.use_textbox) else "OFF")
        self.opt_use_textbox = tk.OptionMenu(self.tkui, self.value_use_textbox, *self.yn_options)
        self.opt_use_textbox.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_textbox.grid(row=11, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_textbox.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.opt_use_textbox.bind("<Leave>", self.hide_tooltip)
        self.value_use_textbox.trace_add("write", (lambda *args: self.changed()))

        self.label_use_kat = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use KAT', font=(self.FONT, 12))
        self.label_use_kat.grid(row=12, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_kat.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to KillFrenzyAvatarText")))
        self.label_use_kat.bind("<Leave>", self.hide_tooltip)
        self.value_use_kat = tk.StringVar(self.tkui)
        self.value_use_kat.set("ON" if bool(self.config.osc.use_kat) else "OFF")
        self.opt_use_kat = tk.OptionMenu(self.tkui, self.value_use_kat, *self.yn_options)
        self.opt_use_kat.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_kat.grid(row=12, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_kat.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to KillFrenzyAvatarText")))
        self.opt_use_kat.bind("<Leave>", self.hide_tooltip)
        self.value_use_kat.trace_add("write", (lambda *args: self.changed()))

        self.label_use_both = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Both', font=(self.FONT, 12))
        self.label_use_both.grid(row=13, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_use_both.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to both options above, if both available and set to 'Yes'.\nIf not, the program will prefer sending to KillFrenzyAvatarText if it is available.")))
        self.label_use_both.bind("<Leave>", self.hide_tooltip)
        self.value_use_both = tk.StringVar(self.tkui)
        self.value_use_both.set("ON" if bool(self.config.osc.use_both) else "OFF")
        self.opt_use_both = tk.OptionMenu(self.tkui, self.value_use_both, *self.yn_options)
        self.opt_use_both.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_both.grid(row=13, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.opt_use_both.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to both options above, if both available and set to 'Yes'.\nIf not, the program will prefer sending to KillFrenzyAvatarText if it is available.")))
        self.opt_use_both.bind("<Leave>", self.hide_tooltip)

        self.label_emotes = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Emotes', font=(self.FONT, 12))
        self.label_emotes.grid(row=14, column=4, padx=PADX_L, pady=PADY, sticky='es')
        self.label_emotes.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use emotes on KAT")))
        self.label_emotes.bind("<Leave>", self.hide_tooltip)
        self.value_emotes = tk.StringVar(self.tkui)
        self.value_emotes.set("ON" if bool(self.config.emotes.enabled) else "OFF")
        self.opt_emotes = tk.OptionMenu(self.tkui, self.value_emotes, *self.yn_options)
        self.opt_emotes.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_emotes.grid(row=14, column=5, padx=PADX_R, pady=PADY, sticky='ws')
        self.button_emotes = tk.Button(self.tkui, text=" ⚙ ", command=self.open_emote_window)
        self.button_emotes.configure(bg="#333333", fg="white", height=1, highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_emotes.grid(row=14, column=6, padx=2, pady=7, sticky='ws')
        self.opt_emotes.bind("<Enter>", (lambda event: self.show_tooltip("If you want to use emotes on KAT")))
        self.opt_emotes.bind("<Leave>", self.hide_tooltip)
        self.button_emotes.bind("<Enter>", (lambda event: self.show_tooltip("Edit the emotes you want to use on KAT")))
        self.button_emotes.bind("<Leave>", self.hide_tooltip)

        self.button_reset_config = tk.Button(self.tkui, text="Reset Settings*", command=self.reset_to_default)
        self.button_reset_config.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=20, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_reset_config.place(relx=0.52, rely=0.95, anchor="center")
        self.button_reset_config.bind("<Enter>", (lambda event: self.show_tooltip("Resets the config to default values. (Does not clear wordreplacement- and emote lists)")))
        self.button_reset_config.bind("<Leave>", self.hide_tooltip)

        self.button_osc_reset_config = tk.Button(self.tkui, text="Reset OSC config", command=self.reset_osc_config)
        self.button_osc_reset_config.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=20, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_osc_reset_config.place(relx=0.71, rely=0.95, anchor="center")
        self.button_osc_reset_config.bind("<Enter>", (lambda event: self.show_tooltip("Resets OSC config by deleting the all the usr_ folders in %APPDATA%\\..\\LocalLow\\VRChat\\VRChat\\OSC")))
        self.button_osc_reset_config.bind("<Leave>", self.hide_tooltip)

        self.button_force_update = tk.Button(self.tkui, text="Force Update*", command=self.reset_osc_config)
        self.button_force_update.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=20, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_force_update.place(relx=0.9, rely=0.95, anchor="center")
        self.button_force_update.bind("<Enter>", (lambda event: self.show_tooltip("Forces the program to update.")))
        self.button_force_update.bind("<Leave>", self.hide_tooltip)

        self.btn_save = tk.Button(self.tkui, text="Save")
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=46, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.215, rely=0.95, anchor="center")

        self.restart_lbl = tk.Label(self.tkui, text="* When changed, the program might restart.")
        self.restart_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.restart_lbl.place(relx=0.01, rely=0.9, anchor="w")

        self.tkui.withdraw()

    def open_emote_window(self):
        _ = EmoteWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_replacement_window(self):
        _ = ReplacementWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_overlay_window(self):
        _ = OverlaySettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_obs_window(self):
        _ = OBSSettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_websocket_window(self):
        _ = WebsocketSettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_audio_window(self):
        _ = AudioSettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)
    
    def open_device_window(self):
        _device = self.value_device.get().lower()
        _index = 0
        if _device != "cpu":
            _index = int(_device[1])
            _device = "cuda"
        _ = DeviceSettingsWindow(self.config, self.config_path, _device, _index, self.icon_path, self.get_coordinates)

    def open_translate_window(self):
        _ = TranslateSettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def open_vad_window(self):
        _ = VADSettingsWindow(self.config, self.config_path, self.icon_path, self.get_coordinates)

    def model_changed(self, *args):
        if self.value_model.get() == "custom":
            self.opt_model.grid_forget()
            self.entry_model.grid(row=4, column=1, padx=0, pady=4, sticky='ws')
        elif self.value_model.get() in self.config.whisper.custom_models:
            self.opt_model.grid_forget()
            self.entry_model.grid(row=4, column=1, padx=0, pady=4, sticky='ws')
            self.entry_model.delete(0, tk.END)
            self.entry_model.insert(0, self.value_model.get())
            
    def entry_model_enter_event(self, text):
        if self.value_model.get() in self.config.whisper.custom_models:
            self.config.whisper.custom_models.remove(self.value_model.get())
            if text != "":
                self.config.whisper.custom_models.append(text)
        if text == "":
            self.entry_model.delete(0, tk.END)
            self.entry_model.grid_forget()
            self.opt_model.grid(row=4, column=1, padx=0, pady=4, sticky='ws')
            self.value_model.set("base")


    def mode_changed(self, *args):
        if self.value_mode.get() == "realtime":
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 5.0)
        elif self.value_mode.get() == "once_continuous":
            self.entry_timeout_time.delete(0, tk.END)
            self.entry_timeout_time.insert(0, 5.0)
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 3.0)
        else:
            self.entry_timeout_time.delete(0, tk.END)
            self.entry_timeout_time.insert(0, 3.0)
            self.entry_pause_threshold.delete(0, tk.END)
            self.entry_pause_threshold.insert(0, 0.8)

    def get_sound_devices(self):
        try:
            res = ["Default"]
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            numdev = info.get("deviceCount")
        except Exception:
            log.error("Failed to get audio devices.")
            log.error(traceback.format_exc())
            return res

        for i in range(0, numdev):
            try:
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    res.append([i, p.get_device_info_by_host_api_device_index(0, i).get('name')])
            except Exception:
                log.error("Failed to get audio device info.")
                log.error(traceback.format_exc())
                res.append([i, "Unknown Device"])
        return res

    def get_audiodevice_index(self):
        option = self.value_mic.get()
        if option != "Default":
            return int(option[1:option.index(',')])
        else:
            return None
        

    def save(self):
        self.config.whisper.device.type = "cuda" if torch.cuda.is_available() and self.value_device.get().lower() != "cpu" else "cpu"
        self.config.whisper.device.index = int(self.value_device.get()[1]) if torch.cuda.is_available() and self.value_device.get().lower() != "cpu" else 0
        self.config.osc.ip = self.entry_osc_ip.get()
        self.config.osc.client_port = int(self.entry_osc_port.get())
        self.config.osc.server_port = int(self.entry_osc_server_port.get())
        if self.value_model.get() == "custom" and self.entry_model.get() != "" and self.entry_model.get() not in self.config.whisper.custom_models:
            self.config.whisper.custom_models.append(self.entry_model.get())
        self.config.whisper.model = self.value_model.get() if self.value_model.get() != "custom" else self.entry_model.get() if self.entry_model.get() != "" else "base"
        self.config.whisper.language = None if self.value_language.get() == "Auto Detect" else self.value_language.get()
        self.config.translator.language = None if self.value_translate.get() == "OFF" else self.value_translate.get()
        self.config.hotkey = self.set_key
        _realtime = 0
        if self.value_mode.get() == "once_continuous":
            _realtime = 1
        elif self.value_mode.get() == "realtime":
            _realtime = 2
        self.config.mode = _realtime
        self.config.listener.dynamic_energy_threshold = True if self.value_det.get() == "ON" else False
        self.config.listener.energy_threshold = float(self.entry_energy_threshold.get())
        self.config.listener.pause_threshold = float(self.entry_pause_threshold.get())
        self.config.text_timeout = float(self.entry_text_timeout_time.get())
        self.config.listener.timeout_time = float(self.entry_timeout_time.get())
        self.config.listener.hold_time = float(self.entry_hold_time.get())
        self.config.listener.phrase_time_limit = float(self.entry_phrase_time_limit.get())
        self.config.listener.microphone_index = self.get_audiodevice_index()
        self.config.osc.use_textbox = True if self.value_use_textbox.get() == "ON" else False
        self.config.osc.use_kat = True if self.value_use_kat.get() == "ON" else False
        self.config.osc.use_both = True if self.value_use_both.get() == "ON" else False
        self.config.audio_feedback.enabled = True if self.value_audio_feedback.get() == "ON" else False
        self.config.emotes.enabled = True if self.value_emotes.get() == "ON" else False
        self.config.overlay.enabled = True if self.value_enable_overlay.get() == "ON" else False
        self.config.wordreplacement.enabled = True if self.value_word_replacements.get() == "ON" else False
        self.config.obs.enabled = True if self.value_obs_source.get() == "ON" else False
        self.config.websocket.enabled = True if self.value_websocket.get() == "ON" else False
        self.config.autocorrect.language = self.value_autocorrect.get() if self.value_autocorrect.get() != "OFF" else None
        self.config.vad.enabled = True if self.value_vad.get() == "ON" else False
        self.config.always_clipboard = True if self.value_clipboard_mode.get() == "Always" else False

        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)

    def reset_to_default(self):
        _config = config_struct()
        _config.wordreplacement.list = self.config.wordreplacement.list
        _config.emotes.list = self.config.emotes.list
        json.dump(_config.to_dict(), open(self.config_path, "w"), indent=4)
        self.restart_func()

    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def open(self):
        log.info("OPEN SETTINGS")
        self.tkui.deiconify()
        self.tkui.mainloop()

    def on_closing(self):
        self.closed = True
        try:
            self.tkui.destroy()
        except tk.TclError:
            pass

    def button_hotkey_pressed(self):
        self.button_hotkey.configure(text="ESC to cancel...", state="disabled", disabledforeground="white")
        self.update()
        key = keyboard.read_hotkey()
        if key != "esc":
            self.set_key = key
        self.button_hotkey.configure(text=self.set_key, state="normal")
        self.update()

    def show_tooltip(self, text):
        # Create a new top-level window with the tooltip text
        self.tooltip_window = tk.Toplevel(self.tkui, bg="black")
        tooltip_label = tk.Label(self.tooltip_window, text=text, fg="white", bg="black", font=(self.FONT, 10))
        tooltip_label.pack()

        # Use the overrideredirect method to remove the window's decorations
        self.tooltip_window.overrideredirect(True)

        # Calculate the coordinates for the tooltip window
        x = self.tkui.winfo_pointerx() + 10
        y = self.tkui.winfo_pointery()
        self.tooltip_window.geometry("+{}+{}".format(x, y))

    def hide_tooltip(self, event):
        # Destroy the tooltip window
        try:
            self.tooltip_window.destroy()
        except:
            pass
        self.tooltip_window = None

    def changed(self):
        if self.value_use_kat.get() == "OFF" or self.value_use_textbox.get() == "OFF":
            self.opt_use_both.configure(state="disabled")
        else:
            self.opt_use_both.configure(state="normal")

    def set_energy_threshold(self, text):
        self.entry_energy_threshold.delete(0, tk.END)
        self.entry_energy_threshold.insert(0, str(text))
        self.update()

    def reset_osc_config(self):
        log.info("RESET OSC CONFIG")
        appdata_path = os.getenv('APPDATA')
        osc_path = appdata_path + "\\..\\LocalLow\\VRChat\\VRChat\\OSC"
        dirs = glob.glob(osc_path + "\\usr_*\\")
        for dir in dirs:
            shutil.rmtree(dir)
    
    def get_coordinates(self):
        return (self.tkui.winfo_x(), self.tkui.winfo_y())

class EmoteWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(650, 390)
        self.tkui.maxsize(650, 390)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Emotes")
        self.tkui.iconbitmap(icon_path)

        self.current_selection = None
        
        self.entry = tk.Entry(self.tkui)
        self.entry.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=55)
        self.entry.place(relx=0.415, rely=0.05, anchor="center")

        self.button = tk.Button(self.tkui, text="Edit")
        self.button.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.edit_entry)
        self.button.place(relx=0.91, rely=0.05, anchor="center")

        self.values = list(self.config.emotes.list.items())
        self.lbox = tk.Listbox(self.tkui, font=(self.FONT, 12), width=70, height=15, bg="#333333", fg="#FFFFFF", selectbackground="#777777", selectforeground="#FFFFFF", bd=0, activestyle="none")
        self.lbox.place(relx=0.5, rely=0.53, anchor="center")
        self.lbox.bind('<<ListboxSelect>>', self.item_selected)
        
        self.update_lbox()

        self.tkui.mainloop()

    def item_selected(self, event):
        if self.lbox.curselection():
            self.current_selection = self.lbox.curselection()[0]
            self.set_entry(self.config.emotes.list[str(self.current_selection)])
            self.button.configure(state="normal")

    def set_entry(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def edit_entry(self):
        self.config.emotes.list[str(self.current_selection)] = self.entry.get()
        self.update_lbox()
        self.button.configure(state="disabled")
        self.entry.delete(0, tk.END)
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)

    def update_lbox(self):
        self.values = list(self.config.emotes.list.items())
        self.lbox.delete(0, tk.END)
        for key, value in self.values:
            self.lbox.insert(tk.END, f"{key}: \"{value}\"")


    def on_closing(self):
        self.tkui.destroy()

class ReplacementWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(760, 430)
        self.tkui.maxsize(760, 430)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Word Replacement")
        self.tkui.iconbitmap(icon_path)

        self.current_selection = None
        self.current_key = None

        self.label_word = tk.Label(self.tkui, text="Expression", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_word.grid(row=0, column=1, padx=5, pady=5, sticky='ws')
        self.label_replace = tk.Label(self.tkui, text="Replacement", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_replace.grid(row=1, column=1, padx=5, pady=5, sticky='ws')
        
        self.entry_word = tk.Entry(self.tkui)
        self.entry_word.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=45)
        self.entry_word.grid(row=0, column=2, padx=5, pady=5, sticky='ws')

        self.entry_replace = tk.Entry(self.tkui)
        self.entry_replace.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666", width=45)
        self.entry_replace.grid(row=1, column=2, padx=5, pady=5, sticky='ws')

        self.button_edit = tk.Button(self.tkui, text="Add")
        self.button_edit.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", command=self.add_edit_entry)
        self.button_edit.grid(row=0, column=3, padx=5, pady=5, sticky='ws')

        self.button_deselect = tk.Button(self.tkui, text="Deselect")
        self.button_deselect.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.button_deselect_pressed)
        self.button_deselect.grid(row=1, column=3, padx=5, pady=5, sticky='ws')

        self.button_delete = tk.Button(self.tkui, text="Remove")
        self.button_delete.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=12, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white", state="disabled", command=self.button_delete_pressed)
        self.button_delete.grid(row=1, column=4, padx=5, pady=5, sticky='ws')

        self.lbox = tk.Listbox(self.tkui, font=(self.FONT, 12), width=82, height=15, bg="#333333", fg="#FFFFFF", selectbackground="#777777", selectforeground="#FFFFFF", bd=0, activestyle="none")
        self.lbox.place(relx=0.5, rely=0.58, anchor="center")
        self.lbox.bind('<<ListboxSelect>>', self.item_selected)
        
        self.update_lbox()

        self.tkui.mainloop()

    def item_selected(self, event):
        if self.lbox.curselection():
            self.button_edit.configure(text="Edit")
            self.entry_replace.delete(0, tk.END)
            self.entry_word.delete(0, tk.END)
            
            self.current_selection = self.lbox.curselection()[0]
            self.current_key = list(self.config.wordreplacement.list)[self.current_selection]

            
            self.entry_word.insert(0, self.current_key)
            self.entry_replace.insert(0, self.config.wordreplacement.list[self.current_key])
            
            self.button_deselect.configure(state="normal")
            self.button_delete.configure(state="normal")

    def add_edit_entry(self):
        if self.entry_word.get() == "" and self.entry_replace.get() == "":
            return

        if self.button_edit["text"] == "Add":
            self.config.wordreplacement.list[self.entry_word.get()] = self.entry_replace.get()
        elif self.current_key != self.entry_word.get() or self.config.wordreplacement.list[self.current_key] != self.entry_replace.get():
            del self.config.wordreplacement.list[self.current_key]
            self.config.wordreplacement.list[self.entry_word.get()] = self.entry_replace.get()
        
        self.button_deselect_pressed()
        self.update_lbox()
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
    
    def button_deselect_pressed(self):
        self.button_edit.configure(text="Add")
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        self.lbox.selection_clear(0, tk.END)
        self.button_deselect.configure(state="disabled")
        self.button_delete.configure(state="disabled")

    def button_delete_pressed(self):
        del self.config.wordreplacement.list[self.current_key]
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.entry_replace.delete(0, tk.END)
        self.entry_word.delete(0, tk.END)
        self.button_deselect_pressed()
        self.update_lbox()
        pass

    def update_lbox(self):
        self.values = list(self.config.wordreplacement.list.items())
        self.lbox.delete(0, tk.END)
        for key, value in self.values:
            self.lbox.insert(tk.END, f"{key} -> {value}")


class OverlaySettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(350, 350)
        self.tkui.maxsize(350, 350)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Overlay Settings")
        self.tkui.iconbitmap(icon_path)

        self.current_selection = None
        self.current_key = None

        self.label_timeout = tk.Label(self.tkui, text="Timeout time", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_timeout.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.entry_timeout = tk.Entry(self.tkui)
        self.entry_timeout.insert(0, self.config.overlay.timeout)
        self.entry_timeout.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_timeout.grid(row=0, column=2, padx=12, pady=5, sticky='ws')

        self.label_pos_x = tk.Label(self.tkui, text="Position X", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_pos_x.grid(row=1, column=1, padx=12, pady=5, sticky='ws')
        self.entry_pos_x = tk.Entry(self.tkui)
        self.entry_pos_x.insert(0, self.config.overlay.pos_x)
        self.entry_pos_x.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_pos_x.grid(row=1, column=2, padx=12, pady=5, sticky='ws')

        self.label_pos_y = tk.Label(self.tkui, text="Position Y", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_pos_y.grid(row=2, column=1, padx=12, pady=5, sticky='ws')
        self.entry_pos_y = tk.Entry(self.tkui)
        self.entry_pos_y.insert(0, self.config.overlay.pos_y)
        self.entry_pos_y.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_pos_y.grid(row=2, column=2, padx=12, pady=5, sticky='ws')

        self.label_size = tk.Label(self.tkui, text="Size", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_size.grid(row=3, column=1, padx=12, pady=5, sticky='ws')
        self.entry_size = tk.Entry(self.tkui)
        self.entry_size.insert(0, self.config.overlay.size)
        self.entry_size.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_size.grid(row=3, column=2, padx=12, pady=5, sticky='ws')

        self.label_distance = tk.Label(self.tkui, text="Distance", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_distance.grid(row=4, column=1, padx=12, pady=5, sticky='ws')
        self.entry_distance = tk.Entry(self.tkui)
        self.entry_distance.insert(0, self.config.overlay.distance)
        self.entry_distance.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_distance.grid(row=4, column=2, padx=12, pady=5, sticky='ws')

        self.label_font_color = tk.Label(self.tkui, text="Font Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_font_color.grid(row=5, column=1, padx=12, pady=5, sticky='ws')
        self.entry_font_color = tk.Entry(self.tkui)
        self.entry_font_color.insert(0, self.config.overlay.font_color)
        self.entry_font_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_font_color.grid(row=5, column=2, padx=12, pady=5, sticky='ws')

        self.label_border_color = tk.Label(self.tkui, text="Border Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_border_color.grid(row=6, column=1, padx=12, pady=5, sticky='ws')
        self.entry_border_color = tk.Entry(self.tkui)
        self.entry_border_color.insert(0, self.config.overlay.border_color)
        self.entry_border_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_border_color.grid(row=6, column=2, padx=12, pady=5, sticky='ws')

        self.label_opacity = tk.Label(self.tkui, text="Opacity", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_opacity.grid(row=7, column=1, padx=12, pady=5, sticky='ws')
        self.entry_opacity = tk.Entry(self.tkui)
        self.entry_opacity.insert(0, self.config.overlay.opacity)
        self.entry_opacity.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_opacity.grid(row=7, column=2, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=39, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.92, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.overlay.timeout = float(self.entry_timeout.get())
        self.config.overlay.pos_x = float(self.entry_pos_x.get())
        self.config.overlay.pos_y = float(self.entry_pos_y.get())
        self.config.overlay.size = float(self.entry_size.get())
        self.config.overlay.distance = float(self.entry_distance.get())
        self.config.overlay.font_color = self.entry_font_color.get()
        self.config.overlay.border_color = self.entry_border_color.get()
        self.config.overlay.opacity = float(self.entry_opacity.get())

        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class OBSSettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(370, 380)
        self.tkui.maxsize(370, 380)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - OBS Source Settings")
        self.tkui.iconbitmap(icon_path)

        self.current_selection = None
        self.current_key = None

        self.label_port = tk.Label(self.tkui, text="Port", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_port.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.entry_port = tk.Entry(self.tkui)
        self.entry_port.insert(0, self.config.obs.port)
        self.entry_port.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_port.grid(row=0, column=2, padx=12, pady=5, sticky='ws')

        self.label_update_interval = tk.Label(self.tkui, text="Update Interval", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_update_interval.grid(row=1, column=1, padx=12, pady=5, sticky='ws')
        self.entry_update_interval = tk.Entry(self.tkui)
        self.entry_update_interval.insert(0, self.config.obs.update_interval)
        self.entry_update_interval.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_update_interval.grid(row=1, column=2, padx=12, pady=5, sticky='ws')

        self.label_font = tk.Label(self.tkui, text="Font", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_font.grid(row=2, column=1, padx=12, pady=5, sticky='ws')
        self.entry_font = tk.Entry(self.tkui)
        self.entry_font.insert(0, self.config.obs.font)
        self.entry_font.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_font.grid(row=2, column=2, padx=12, pady=5, sticky='ws')

        self.label_color = tk.Label(self.tkui, text="Color", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_color.grid(row=3, column=1, padx=12, pady=5, sticky='ws')
        self.entry_color = tk.Entry(self.tkui)
        self.entry_color.insert(0, self.config.obs.color)
        self.entry_color.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_color.grid(row=3, column=2, padx=12, pady=5, sticky='ws')

        self.label_align = tk.Label(self.tkui, text="Align", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_align.grid(row=4, column=1, padx=12, pady=5, sticky='ws')
        self.value_align = tk.StringVar(self.tkui)
        self.value_align.set(self.config.obs.align)
        self.opt_align = tk.OptionMenu(self.tkui, self.value_align, *["center", "left", "right"])
        self.opt_align.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_align.grid(row=4, column=2, padx=12, pady=5, sticky='ws')

        self.label_size = tk.Label(self.tkui, text="Font Size", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_size.grid(row=5, column=1, padx=12, pady=5, sticky='ws')
        self.entry_size = tk.Entry(self.tkui)
        self.entry_size.insert(0, self.config.obs.size)
        self.entry_size.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_size.grid(row=5, column=2, padx=12, pady=5, sticky='ws')

        self.label_emotes = tk.Label(self.tkui, text="Emotes", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_emotes.grid(row=6, column=1, padx=12, pady=5, sticky='ws')
        self.value_emotes = tk.StringVar(self.tkui)
        self.value_emotes.set("OFF" if not self.config.obs.seventv.enabled else "ON")
        self.opt_emotes = tk.OptionMenu(self.tkui, self.value_emotes, *["OFF", "ON"])
        self.opt_emotes.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_emotes.grid(row=6, column=2, padx=12, pady=5, sticky='ws')

        self.label_emoteid = tk.Label(self.tkui, text="Emote Set ID", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_emoteid.grid(row=7, column=1, padx=12, pady=5, sticky='ws')
        self.entry_emoteid = tk.Entry(self.tkui)
        self.entry_emoteid.insert(0, self.config.obs.seventv.emote_set)
        self.entry_emoteid.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_emoteid.grid(row=7, column=2, padx=12, pady=5, sticky='ws')

        self.label_case_sensitive = tk.Label(self.tkui, text="Case Sensitive", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_case_sensitive.grid(row=8, column=1, padx=12, pady=5, sticky='ws')
        self.value_case_sensitive = tk.StringVar(self.tkui)
        self.value_case_sensitive.set("OFF" if not self.config.obs.seventv.case_sensitive else "ON")
        self.opt_case_sensitive = tk.OptionMenu(self.tkui, self.value_case_sensitive, *["OFF", "ON"])
        self.opt_case_sensitive.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_case_sensitive.grid(row=8, column=2, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=43, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.94, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.obs.port = int(self.entry_port.get())
        self.config.obs.update_interval = int(self.entry_update_interval.get())
        self.config.obs.font = self.entry_font.get()
        self.config.obs.color = self.entry_color.get()
        self.config.obs.align = self.value_align.get()
        self.config.obs.size = int(self.entry_size.get())
        self.config.obs.seventv.enabled = True if self.value_emotes.get() == "ON" else False
        self.config.obs.seventv.emote_set = self.entry_emoteid.get()
        self.config.obs.seventv.case_sensitive = True if self.value_case_sensitive.get() == "ON" else False

        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class WebsocketSettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(280, 70)
        self.tkui.maxsize(280, 70)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Websocket Settings")
        self.tkui.iconbitmap(icon_path)

        self.label_port = tk.Label(self.tkui, text="Port", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_port.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.entry_port = tk.Entry(self.tkui)
        self.entry_port.insert(0, self.config.websocket.port)
        self.entry_port.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_port.grid(row=0, column=2, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=33, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.74, anchor="center")
    
    def save(self):
        self.config.websocket.port = int(self.entry_port.get())

        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()


class DeviceSettingsWindow:
    def __init__(self, conf: config_struct, config_path, device, device_index, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(430, 190)
        self.tkui.maxsize(430, 190)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Device Settings")
        self.tkui.iconbitmap(icon_path)

        self.devices_list = []
        self.value_device = tk.StringVar(self.tkui)

        self.label_comptype = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Compute Type', font=(self.FONT, 12))
        self.label_comptype.grid(row=0, column=0, padx=12, pady=5, sticky='es')
        self.options_comptype = list(get_supported_compute_types(device, device_index))
        self.value_comptype = tk.StringVar(self.tkui)
        if self.config.whisper.device.compute_type is None:
            self.value_comptype.set(get_best_compute_type(device, device_index))
        else:
            self.value_comptype.set(self.config.whisper.device.compute_type)
        self.opt_comptype = tk.OptionMenu(self.tkui, self.value_comptype, *self.options_comptype)
        self.opt_comptype.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_comptype.grid(row=0, column=1, padx=12, pady=5, sticky='ws')

        self.label_cpu_threads = tk.Label(self.tkui, text="CPU Threads", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_cpu_threads.grid(row=1, column=0, padx=12, pady=5, sticky='ws')
        self.entry_cpu_threads = tk.Entry(self.tkui)
        self.entry_cpu_threads.insert(0, self.config.whisper.device.cpu_threads)
        self.entry_cpu_threads.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_cpu_threads.grid(row=1, column=1, padx=12, pady=5, sticky='ws')

        self.label_num_workers = tk.Label(self.tkui, text="Num Workers", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_num_workers.grid(row=2, column=0, padx=12, pady=5, sticky='ws')
        self.entry_num_workers = tk.Entry(self.tkui)
        self.entry_num_workers.insert(0, self.config.whisper.device.num_workers)
        self.entry_num_workers.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_num_workers.grid(row=2, column=1, padx=12, pady=5, sticky='ws')

        self.label_max_transciption_time = tk.Label(self.tkui, text="Max Transciption Time", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_max_transciption_time.grid(row=3, column=0, padx=12, pady=5, sticky='ws')
        self.entry_max_transciption_time = tk.Entry(self.tkui)
        self.entry_max_transciption_time.insert(0, self.config.whisper.max_transciption_time)
        self.entry_max_transciption_time.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_max_transciption_time.grid(row=3, column=1, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=49, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.88, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.whisper.device.compute_type = self.value_comptype.get()
        num_threads = int(self.entry_cpu_threads.get())
        max_cpu_threads = cpu_count()
        self.config.whisper.device.cpu_threads = num_threads if num_threads <= max_cpu_threads else max_cpu_threads
        self.config.whisper.device.num_workers = int(self.entry_num_workers.get())
        self.config.whisper.max_transciption_time = float(self.entry_max_transciption_time.get())

        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class AudioSettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.yn_options = ["ON", "OFF"]

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(350, 570)
        self.tkui.maxsize(350, 570)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Audio Feedback Settings")
        self.tkui.iconbitmap(icon_path)

        self.label_clear = tk.Label(self.tkui, text="clear", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_clear.grid(row=0, column=0, padx=12, pady=5, sticky='ws')
        self.label_clear_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_clear_gain.grid(row=1, column=0, padx=12, pady=5, sticky='e')
        self.value_clear = tk.StringVar(self.tkui)
        self.value_clear.set("ON" if self.config.audio_feedback.sound_clear.enabled else "OFF")
        self.opt_clear = tk.OptionMenu(self.tkui, self.value_clear, *self.yn_options)
        self.opt_clear.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_clear.grid(row=0, column=1, padx=12, pady=5, sticky='ws')
        self.scale_clear = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_clear.grid(row=1, column=1, padx=12, pady=5, sticky='ws')
        self.scale_clear.set(self.config.audio_feedback.sound_clear.gain)

        self.label_donelisten = tk.Label(self.tkui, text="donelisten", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_donelisten.grid(row=2, column=0, padx=12, pady=5, sticky='ws')
        self.label_donelisten_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_donelisten_gain.grid(row=3, column=0, padx=12, pady=5, sticky='e')
        self.value_donelisten = tk.StringVar(self.tkui)
        self.value_donelisten.set("ON" if self.config.audio_feedback.sound_donelisten.enabled else "OFF")
        self.opt_donelisten = tk.OptionMenu(self.tkui, self.value_donelisten, *self.yn_options)
        self.opt_donelisten.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_donelisten.grid(row=2, column=1, padx=12, pady=5, sticky='ws')
        self.scale_donelisten = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_donelisten.grid(row=3, column=1, padx=12, pady=5, sticky='ws')
        self.scale_donelisten.set(self.config.audio_feedback.sound_donelisten.gain)

        self.label_finished = tk.Label(self.tkui, text="finished", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_finished.grid(row=4, column=0, padx=12, pady=5, sticky='ws')
        self.label_finished_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_finished_gain.grid(row=5, column=0, padx=12, pady=5, sticky='e')
        self.value_finished = tk.StringVar(self.tkui)
        self.value_finished.set("ON" if self.config.audio_feedback.sound_finished.enabled else "OFF")
        self.opt_finished = tk.OptionMenu(self.tkui, self.value_finished, *self.yn_options)
        self.opt_finished.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_finished.grid(row=4, column=1, padx=12, pady=5, sticky='ws')
        self.scale_finished = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_finished.grid(row=5, column=1, padx=12, pady=5, sticky='ws')
        self.scale_finished.set(self.config.audio_feedback.sound_finished.gain)

        self.label_listen = tk.Label(self.tkui, text="listen", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_listen.grid(row=6, column=0, padx=12, pady=5, sticky='ws')
        self.label_listen_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_listen_gain.grid(row=7, column=0, padx=12, pady=5, sticky='e')
        self.value_listen = tk.StringVar(self.tkui)
        self.value_listen.set("ON" if self.config.audio_feedback.sound_listen.enabled else "OFF")
        self.opt_listen = tk.OptionMenu(self.tkui, self.value_listen, *self.yn_options)
        self.opt_listen.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_listen.grid(row=6, column=1, padx=12, pady=5, sticky='ws')
        self.scale_listen = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_listen.grid(row=7, column=1, padx=12, pady=5, sticky='ws')
        self.scale_listen.set(self.config.audio_feedback.sound_listen.gain)

        self.label_timeout = tk.Label(self.tkui, text="timeout", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_timeout.grid(row=8, column=0, padx=12, pady=5, sticky='ws')
        self.label_timeout_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_timeout_gain.grid(row=9, column=0, padx=12, pady=5, sticky='e')
        self.value_timeout = tk.StringVar(self.tkui)
        self.value_timeout.set("ON" if self.config.audio_feedback.sound_timeout.enabled else "OFF")
        self.opt_timeout = tk.OptionMenu(self.tkui, self.value_timeout, *self.yn_options)
        self.opt_timeout.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_timeout.grid(row=8, column=1, padx=12, pady=5, sticky='ws')
        self.scale_timeout = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_timeout.grid(row=9, column=1, padx=12, pady=5, sticky='ws')
        self.scale_timeout.set(self.config.audio_feedback.sound_timeout.gain)

        self.label_timeout_text = tk.Label(self.tkui, text="timeout_text", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_timeout_text.grid(row=10, column=0, padx=12, pady=5, sticky='ws')
        self.label_timeout_text_gain = tk.Label(self.tkui, text="gain (dB)", bg="#333333", fg="#888888", font=(self.FONT, 12))
        self.label_timeout_text_gain.grid(row=11, column=0, padx=12, pady=5, sticky='e')
        self.value_timeout_text = tk.StringVar(self.tkui)
        self.value_timeout_text.set("ON" if self.config.audio_feedback.sound_timeout_text.enabled else "OFF")
        self.opt_timeout_text = tk.OptionMenu(self.tkui, self.value_timeout_text, *self.yn_options)
        self.opt_timeout_text.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_timeout_text.grid(row=10, column=1, padx=12, pady=5, sticky='ws')
        self.scale_timeout_text = tk.Scale(self.tkui, from_=-50, to=50, orient=tk.HORIZONTAL, bg="#333333", fg="white", highlightthickness=0, length=190)
        self.scale_timeout_text.grid(row=11, column=1, padx=12, pady=5, sticky='ws')
        self.scale_timeout_text.set(self.config.audio_feedback.sound_timeout_text.gain)

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=40, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.958, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.audio_feedback.sound_clear.enabled = self.value_clear.get() == "ON"
        self.config.audio_feedback.sound_clear.gain = self.scale_clear.get()
        self.config.audio_feedback.sound_donelisten.enabled = self.value_donelisten.get() == "ON"
        self.config.audio_feedback.sound_donelisten.gain = self.scale_donelisten.get()
        self.config.audio_feedback.sound_finished.enabled = self.value_finished.get() == "ON"
        self.config.audio_feedback.sound_finished.gain = self.scale_finished.get()
        self.config.audio_feedback.sound_listen.enabled = self.value_listen.get() == "ON"
        self.config.audio_feedback.sound_listen.gain = self.scale_listen.get()
        self.config.audio_feedback.sound_timeout.enabled = self.value_timeout.get() == "ON"
        self.config.audio_feedback.sound_timeout.gain = self.scale_timeout.get()
        self.config.audio_feedback.sound_timeout_text.enabled = self.value_timeout_text.get() == "ON"
        self.config.audio_feedback.sound_timeout_text.gain = self.scale_timeout_text.get()
        
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class TranslateSettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(340, 240)
        self.tkui.maxsize(340, 240)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Translation Device Settings")
        self.tkui.iconbitmap(icon_path)

        self.devices_list = []
        self.value_device = tk.StringVar(self.tkui)

        if torch.cuda.is_available():
            for i in range(0, torch.cuda.device_count()):
                self.devices_list.append((i, torch.cuda.get_device_name(i)))
            if self.config.translator.device.type != "cpu":
                _index = int(self.config.translator.device.index)
                self.value_device.set(self.devices_list[_index])

        if self.config.translator.device.type == "cpu" or not torch.cuda.is_available():
            self.value_device.set("CPU")

        self.devices_list.append("CPU")

        self.label_device = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Device', font=(self.FONT, 12))
        self.label_device.grid(row=0, column=0, padx=12, pady=5, sticky='es')
        self.opt_device = tk.OptionMenu(self.tkui, self.value_device, *self.devices_list)
        self.opt_device.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_device.grid(row=0, column=1, padx=12, pady=5, sticky='ws')

        self.model_list = ["small", "large"]
        self.value_model = tk.StringVar(self.tkui)
        self.value_model.set(self.config.translator.model)
        self.label_model = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Model', font=(self.FONT, 12))
        self.label_model.grid(row=1, column=0, padx=12, pady=5, sticky='es')
        self.opt_model = tk.OptionMenu(self.tkui, self.value_model, *self.model_list)
        self.opt_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_model.grid(row=1, column=1, padx=12, pady=5, sticky='ws')

        self.label_comptype = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Compute Type', font=(self.FONT, 12))
        self.label_comptype.grid(row=2, column=0, padx=12, pady=5, sticky='es')
        self.options_comptype = list(get_supported_compute_types(self.config.translator.device.type, self.config.translator.device.index))
        self.value_comptype = tk.StringVar(self.tkui)
        if self.config.translator.device.compute_type is None:
            self.value_comptype.set(get_best_compute_type(self.config.translator.device.type, self.config.translator.device.index))
        else:
            self.value_comptype.set(self.config.translator.device.compute_type)
        self.opt_comptype = tk.OptionMenu(self.tkui, self.value_comptype, *self.options_comptype)
        self.opt_comptype.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=18, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_comptype.grid(row=2, column=1, padx=12, pady=5, sticky='ws')

        self.label_cpu_threads = tk.Label(self.tkui, text="CPU Threads", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_cpu_threads.grid(row=3, column=0, padx=12, pady=5, sticky='ws')
        self.entry_cpu_threads = tk.Entry(self.tkui)
        self.entry_cpu_threads.insert(0, self.config.translator.device.cpu_threads)
        self.entry_cpu_threads.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_cpu_threads.grid(row=3, column=1, padx=12, pady=5, sticky='ws')

        self.label_num_workers = tk.Label(self.tkui, text="Num Workers", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_num_workers.grid(row=4, column=0, padx=12, pady=5, sticky='ws')
        self.entry_num_workers = tk.Entry(self.tkui)
        self.entry_num_workers.insert(0, self.config.translator.device.num_workers)
        self.entry_num_workers.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_num_workers.grid(row=4, column=1, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=40, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.9, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.translator.device.type = "cuda" if torch.cuda.is_available() and self.value_device.get().lower() != "cpu" else "cpu"
        self.config.translator.device.index = int(self.value_device.get()[1]) if torch.cuda.is_available() and self.value_device.get().lower() != "cpu" else 0
        self.config.translator.model = self.value_model.get()
        self.config.translator.device.compute_type = self.value_comptype.get()
        self.config.translator.device.cpu_threads = int(self.entry_cpu_threads.get())
        self.config.translator.device.num_workers = int(self.entry_num_workers.get())
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()

class VADSettingsWindow:
    def __init__(self, conf: config_struct, config_path, icon_path, get_coordinates):
        self.config_path = config_path
        self.config: config_struct = conf
        self.FONT = "Cascadia Code"

        self.tkui = tk.Tk()
        coordinates = get_coordinates()
        self.tkui.geometry(f"+{coordinates[0]}+{coordinates[1]}")
        self.tkui.minsize(450, 150)
        self.tkui.maxsize(450, 150)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Translation Device Settings")
        self.tkui.iconbitmap(icon_path)

        self.label_threshold = tk.Label(self.tkui, text="threshold", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_threshold.grid(row=0, column=0, padx=12, pady=5, sticky='ws')
        self.entry_threshold = tk.Entry(self.tkui)
        self.entry_threshold.insert(0, self.config.vad.parameters.threshold)
        self.entry_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_threshold.grid(row=0, column=1, padx=12, pady=5, sticky='ws')

        self.label_min_speech_duration_ms = tk.Label(self.tkui, text="min_speech_duration_ms", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_min_speech_duration_ms.grid(row=1, column=0, padx=12, pady=5, sticky='ws')
        self.entry_min_speech_duration_ms = tk.Entry(self.tkui)
        self.entry_min_speech_duration_ms.insert(0, self.config.vad.parameters.min_speech_duration_ms)
        self.entry_min_speech_duration_ms.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_min_speech_duration_ms.grid(row=1, column=1, padx=12, pady=5, sticky='ws')

        self.label_min_silence_duration_ms = tk.Label(self.tkui, text="min_silence_duration_ms", bg="#333333", fg="white", font=(self.FONT, 12))
        self.label_min_silence_duration_ms.grid(row=2, column=0, padx=12, pady=5, sticky='ws')
        self.entry_min_silence_duration_ms = tk.Entry(self.tkui)
        self.entry_min_silence_duration_ms.insert(0, self.config.vad.parameters.min_silence_duration_ms)
        self.entry_min_silence_duration_ms.configure(bg="#333333", fg="white", font=(self.FONT, 12), highlightthickness=0, insertbackground="#666666")
        self.entry_min_silence_duration_ms.grid(row=2, column=1, padx=12, pady=5, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save", command=self.save)
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=53, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.88, anchor="center")

        self.tkui.mainloop()

    def save(self):
        self.config.vad.parameters.threshold = float(self.entry_threshold.get())
        self.config.vad.parameters.min_speech_duration_ms = int(self.entry_min_speech_duration_ms.get())
        self.config.vad.parameters.min_silence_duration_ms = int(self.entry_min_silence_duration_ms.get())
        json.dump(self.config.to_dict(), open(self.config_path, "w"), indent=4)
        self.on_closing()

    def on_closing(self):
        self.tkui.destroy()