import tkinter as tk
import json
import os
import sys
import whisper
import pyaudio

class settings_ui:
    def __init__(self, config, config_path):
        self.config = config
        self.config_path = config_path
        FONT = "Cascadia Code"
        PADX = '15'
        PADY = '5'
        self.yn_options = ["yes", "no"]
        self.whisper_models = whisper.available_models()
        self.whisper_models = [x for x in self.whisper_models if ".en" not in x]


        self.tkui = tk.Tk()
        self.tkui.minsize(570, 700)
        self.tkui.maxsize(570, 700)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Settings")


        self.label_osc_ip = tk.Label(master=self.tkui, bg="#333333", fg="white", text='osc_ip', font=(FONT, 15))
        self.label_osc_ip.grid(row=0, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_osc_ip = tk.Entry(self.tkui)
        self.entry_osc_ip.insert(0, self.config["osc_ip"])
        self.entry_osc_ip.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_ip.grid(row=0, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_osc_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='osc_port', font=(FONT, 15))
        self.label_osc_port.grid(row=1, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_osc_port = tk.Entry(self.tkui)
        self.entry_osc_port.insert(0, self.config["osc_port"])
        self.entry_osc_port.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_port.grid(row=1, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_osc_server_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='osc_server_port', font=(FONT, 15))
        self.label_osc_server_port.grid(row=2, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_osc_server_port = tk.Entry(self.tkui)
        self.entry_osc_server_port.insert(0, self.config["osc_server_port"])
        self.entry_osc_server_port.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_server_port.grid(row=2, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_model = tk.Label(master=self.tkui, bg="#333333", fg="white", text='model', font=(FONT, 15))
        self.label_model.grid(row=3, column=0, padx=PADX, pady=PADY, sticky='es')
        self.value_model = tk.StringVar(self.tkui)
        self.value_model.set(self.config["model"])
        self.opt_model = tk.OptionMenu(self.tkui, self.value_model, *self.whisper_models)
        self.opt_model.configure(bg="#333333", fg="white", font=(FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_model.grid(row=3, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_language = tk.Label(master=self.tkui, bg="#333333", fg="white", text='language', font=(FONT, 15))
        self.label_language.grid(row=4, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_language = tk.Entry(self.tkui)
        self.entry_language.insert(0, self.config["language"])
        self.entry_language.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_language.grid(row=4, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_hotkey = tk.Label(master=self.tkui, bg="#333333", fg="white", text='hotkey', font=(FONT, 15))
        self.label_hotkey.grid(row=5, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_hotkey = tk.Entry(self.tkui)
        self.entry_hotkey.insert(0, self.config["hotkey"])
        self.entry_hotkey.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_hotkey.grid(row=5, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_det = tk.Label(master=self.tkui, bg="#333333", fg="white", text='dynamic_energy_threshold', font=(FONT, 15))
        self.label_det.grid(row=6, column=0, padx=PADX, pady=PADY, sticky='es')
        self.value_det = tk.StringVar(self.tkui)
        self.value_det.set("yes" if bool(self.config["dynamic_energy_threshold"]) else "no")
        self.opt_det = tk.OptionMenu(self.tkui, self.value_det, *self.yn_options)
        self.opt_det.configure(bg="#333333", fg="white", font=(FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_det.grid(row=6, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_energy_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='energy_threshold', font=(FONT, 15))
        self.label_energy_threshold.grid(row=7, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_energy_threshold = tk.Entry(self.tkui)
        self.entry_energy_threshold.insert(0, self.config["energy_threshold"])
        self.entry_energy_threshold.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_energy_threshold.grid(row=7, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_pause_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='pause_threshold', font=(FONT, 15))
        self.label_pause_threshold.grid(row=8, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_pause_threshold = tk.Entry(self.tkui)
        self.entry_pause_threshold.insert(0, self.config["pause_threshold"])
        self.entry_pause_threshold.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_pause_threshold.grid(row=8, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_timeout_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='timeout_time', font=(FONT, 15))
        self.label_timeout_time.grid(row=9, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_timeout_time = tk.Entry(self.tkui)
        self.entry_timeout_time.insert(0, self.config["timeout_time"])
        self.entry_timeout_time.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_timeout_time.grid(row=9, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_hold_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='hold_time', font=(FONT, 15))
        self.label_hold_time.grid(row=10, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_hold_time = tk.Entry(self.tkui)
        self.entry_hold_time.insert(0, self.config["hold_time"])
        self.entry_hold_time.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_hold_time.grid(row=10, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_max_transcribe_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='max_transcribe_time', font=(FONT, 15))
        self.label_max_transcribe_time.grid(row=11, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_max_transcribe_time = tk.Entry(self.tkui)
        self.entry_max_transcribe_time.insert(0, self.config["max_transcribe_time"])
        self.entry_max_transcribe_time.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_max_transcribe_time.grid(row=11, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_mic = tk.Label(master=self.tkui, bg="#333333", fg="white", text='microphone', font=(FONT, 15))
        self.label_mic.grid(row=12, column=0, padx=PADX, pady=PADY, sticky='es')
        self.option_index = option_index = 0 if self.config["microphone_index"] is None else int(self.config["microphone_index"]) + 1
        self.options_mic = self.get_sound_devices()
        self.value_mic = tk.StringVar(self.tkui)
        self.value_mic.set(self.options_mic[option_index])
        self.opt_mic = tk.OptionMenu(self.tkui, self.value_mic, *self.options_mic)
        self.opt_mic.configure(bg="#333333", fg="white", font=(FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mic.grid(row=12, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_banned_words = tk.Label(master=self.tkui, bg="#333333", fg="white", text='banned_words', font=(FONT, 15))
        self.label_banned_words.grid(row=13, column=0, padx=PADX, pady=PADY, sticky='es')
        self.entry_banned_words = tk.Entry(self.tkui)
        self.entry_banned_words.insert(0, ','.join(self.config["banned_words"]))
        self.entry_banned_words.configure(bg="#333333", fg="white", font=(FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_banned_words.grid(row=13, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_use_textbox = tk.Label(master=self.tkui, bg="#333333", fg="white", text='use_textbox', font=(FONT, 15))
        self.label_use_textbox.grid(row=14, column=0, padx=PADX, pady=PADY, sticky='es')
        self.value_use_textbox = tk.StringVar(self.tkui)
        self.value_use_textbox.set("yes" if bool(self.config["use_textbox"]) else "no")
        self.opt_use_textbox = tk.OptionMenu(self.tkui, self.value_use_textbox, *self.yn_options)
        self.opt_use_textbox.configure(bg="#333333", fg="white", font=(FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_textbox.grid(row=14, column=1, padx=PADX, pady=PADY, sticky='ws')


        self.label_use_kat = tk.Label(master=self.tkui, bg="#333333", fg="white", text='use_kat', font=(FONT, 15))
        self.label_use_kat.grid(row=15, column=0, padx=PADX, pady=PADY, sticky='es')
        self.value_use_kat = tk.StringVar(self.tkui)
        self.value_use_kat.set("yes" if bool(self.config["use_kat"]) else "no")
        self.opt_use_kat = tk.OptionMenu(self.tkui, self.value_use_kat, *self.yn_options)
        self.opt_use_kat.configure(bg="#333333", fg="white", font=(FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_kat.grid(row=15, column=1, padx=PADX, pady=PADY, sticky='ws')


    def get_sound_devices(self):
        res = ["Default"]
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdev = info.get("deviceCount")

        for i in range(0, numdev):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                res.append([i, p.get_device_info_by_host_api_device_index(0, i).get('name')])
                print(f"Input Device id {i} - {p.get_device_info_by_host_api_device_index(0, i).get('name')}")

        return res


    def get_audiodevice_index(self):
        option = self.value_mic.get()
        if option != "Default":
            return int(option[1:option.index(',')])
        else:
            return None


    def get_banned_words(self):
        res = self.entry_banned_words.get()
        if res == '':
            return []
        else:
            return res.split(',')


    def save(self):
        self.config["osc_ip"] = self.entry_osc_ip.get()
        self.config["osc_port"] = int(self.entry_osc_port.get())
        self.config["osc_server_port"] = int(self.entry_osc_server_port.get())
        self.config["model"] = self.value_model.get()
        self.config["language"] = self.entry_language.get()
        self.config["hotkey"] = self.entry_hotkey.get()
        self.config["dynamic_energy_threshold"] = True if self.value_det.get() == "yes" else False
        self.config["energy_threshold"] = int(self.entry_energy_threshold.get())
        self.config["pause_threshold"] = float(self.entry_pause_threshold.get())
        self.config["timeout_time"] = float(self.entry_timeout_time.get())
        self.config["hold_time"] = float(self.entry_hold_time.get())
        self.config["max_transcribe_time"] = float(self.entry_max_transcribe_time.get())
        self.config["microphone_index"] = self.get_audiodevice_index()
        self.config["banned_words"] = self.get_banned_words()
        self.config["use_textbox"] = True if self.value_use_textbox.get() == "yes" else False
        self.config["use_kat"] = True if self.value_use_kat.get() == "yes" else False

        json.dump(self.config, open(self.config_path, "w"), indent=4)

    def run(self):
        self.tkui.mainloop()
    
    def on_closing(self):
        self.save()
        self.closed = True
        self.tkui.destroy()