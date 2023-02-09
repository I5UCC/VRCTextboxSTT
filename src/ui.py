import tkinter as tk
import json
import whisper
from whisper import tokenizer
import pyaudio
import keyboard

class MainWindow(object):
    def __init__(self, version):

        self.FONT = "Cascadia Code"
        print(version)

        self.tkui = tk.Tk()
        self.tkui.minsize(810, 380)
        self.tkui.maxsize(810, 380)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT")

        self.text_lbl = tk.Label(self.tkui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 27))
        self.text_lbl.place(relx=0.5, rely=0.45, anchor="center")

        self.conf_lbl = tk.Label(self.tkui, text=f"Loading...")
        self.conf_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.conf_lbl.place(relx=0.01, rely=0.935, anchor="w")

        self.ver_lbl = tk.Label(self.tkui, text=f" VRCTextboxSTT {version} by I5UCC")
        self.ver_lbl.configure(bg="#333333", fg="#666666", font=(self.FONT, 10))
        self.ver_lbl.place(relx=0.99, rely=0.05, anchor="e")

        self.status_lbl = tk.Label(self.tkui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=(self.FONT, 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.tkui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=(self.FONT, 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.btn_settings = tk.Button(self.tkui, text="Settings")
        self.btn_settings.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=20, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_settings.place(relx=0.99, rely=0.94, anchor="e")

        self.textfield = tk.Entry(self.tkui)
        self.textfield.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=25, highlightthickness=0, insertbackground="#666666")
        self.textfield.place(relx=0.5, rely=0.845, anchor="center", width=792, height=25)
        self.update()

    def open(self):
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
        print(text)

    def set_text_label(self, text):
        self.text_lbl.configure(text=text)
        self.update()

    def loading_status(self, s: str):
        try:
            self.set_text_label(f"Downloading Model:{s[s.rindex('|')+1:]}")
        except Exception:
            self.set_text_label("Done.")

    def set_conf_label(self, ip, port, server_port, ovr_initialized, use_cpu, model):
        self.conf_lbl.configure(text=f"OSC: {ip}#{port}:{server_port}, OVR: {'Connected' if ovr_initialized else 'Failed to Connect'}, Device: {'CPU' if use_cpu else 'GPU'}, Model: {model}")
        self.update()

    def clear_textfield(self):
        self.textfield.delete(0, tk.END)
        self.update()

    def on_closing(self):
        self.tkui.destroy()

    def set_button_enabled(self, state=False):
        if state:
            self.btn_settings.configure(state="normal")
        else:
            self.btn_settings.configure(state="disabled")


class SettingsWindow:
    def __init__(self, config, config_path):
        self.languages = sorted(tokenizer.TO_LANGUAGE_CODE.keys())
        
        self.config = config
        self.config_path = config_path
        self.FONT = "Cascadia Code"
        PADX_R = '0'
        PADX_L = '20'
        PADY = '4'
        self.yn_options = ["yes", "no"]
        self.whisper_models = whisper.available_models()
        self.whisper_models = [x for x in self.whisper_models if ".en" not in x]
        self.tooltip_window = None
        self.ew = None

        self.tkui = tk.Tk()
        self.tkui.minsize(480, 730)
        self.tkui.maxsize(480, 730)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Settings")

        self.label_osc_ip = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC IP', font=(self.FONT, 12))
        self.label_osc_ip.grid(row=0, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_osc_ip = tk.Entry(self.tkui)
        self.entry_osc_ip.insert(0, self.config["osc_ip"])
        self.entry_osc_ip.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_ip.grid(row=0, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_osc_ip.bind("<Enter>", (lambda event: self.show_tooltip("IP to send the OSC information to.")))
        self.label_osc_ip.bind("<Leave>", self.hide_tooltip)

        self.label_osc_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Port', font=(self.FONT, 12))
        self.label_osc_port.grid(row=1, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_osc_port = tk.Entry(self.tkui)
        self.entry_osc_port.insert(0, self.config["osc_port"])
        self.entry_osc_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_osc_port.grid(row=1, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_osc_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to send the OSC information to.")))
        self.label_osc_port.bind("<Leave>", self.hide_tooltip)

        self.label_osc_server_port = tk.Label(master=self.tkui, bg="#333333", fg="white", text='OSC Server Port', font=(self.FONT, 12))
        self.label_osc_server_port.grid(row=2, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_osc_server_port = tk.Entry(self.tkui)
        self.entry_osc_server_port.insert(0, self.config["osc_server_port"])
        self.entry_osc_server_port.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23, disabledbackground="#444444")
        self.entry_osc_server_port.grid(row=2, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_osc_server_port.bind("<Enter>", (lambda event: self.show_tooltip("Port to get the OSC information from.\nUsed to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar.\nOnly used if KAT Sync Params is set to 'Auto Detect' and use KAT set to 'Yes'")))
        self.label_osc_server_port.bind("<Leave>", self.hide_tooltip)

        self.label_model = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Model', font=(self.FONT, 12))
        self.label_model.grid(row=3, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_model = tk.StringVar(self.tkui)
        self.value_model.set(self.config["model"])
        self.opt_model = tk.OptionMenu(self.tkui, self.value_model, *self.whisper_models)
        self.opt_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_model.grid(row=3, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_model.bind("<Enter>", (lambda event: self.show_tooltip("What model of whisper to use. \nI'd recommend not going over 'tiny,base,small'\n as it will significantly impact the transcription time.")))
        self.label_model.bind("<Leave>", self.hide_tooltip)

        self.label_language = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Language', font=(self.FONT, 12))
        self.label_language.grid(row=4, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_language = tk.StringVar(self.tkui)
        self.value_language.set(self.config["language"])
        self.opt_language = tk.OptionMenu(self.tkui, self.value_language, *self.languages)
        self.opt_language.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_language.grid(row=4, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_language.bind("<Enter>", (lambda event: self.show_tooltip("Language to use, 'english' will be faster then other languages. \nLeaving it empty will let the program decide what language you are speaking.")))
        self.label_language.bind("<Leave>", self.hide_tooltip)

        self.label_hotkey = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hotkey', font=(self.FONT, 12))
        self.label_hotkey.grid(row=5, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.set_key = self.config["hotkey"]
        self.button_hotkey = tk.Button(self.tkui, text=self.config["hotkey"], command=self.button_hotkey_pressed)
        self.button_hotkey.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=23, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_hotkey.grid(row=5, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_hotkey.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nKlick on the button and press the button you want to use.")))
        self.label_hotkey.bind("<Leave>", self.hide_tooltip)

        self.label_continuous = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Transcription Mode', font=(self.FONT, 12))
        self.label_continuous.grid(row=6, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_continuous = tk.StringVar(self.tkui)
        self.value_continuous.set("continuous" if bool(self.config["continuous"]) else "once")
        self.opt_continuous = tk.OptionMenu(self.tkui, self.value_continuous, *["continuous", "once"])
        self.opt_continuous.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_continuous.grid(row=6, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_continuous.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.label_continuous.bind("<Leave>", self.hide_tooltip)
        self.value_continuous.trace_add("write", (lambda *args: self.changed()))

        self.label_det = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Dynamic Energy Threshold', font=(self.FONT, 12))
        self.label_det.grid(row=7, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_det = tk.StringVar(self.tkui)
        self.value_det.set("yes" if bool(self.config["dynamic_energy_threshold"]) else "no")
        self.opt_det = tk.OptionMenu(self.tkui, self.value_det, *self.yn_options)
        self.opt_det.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_det.grid(row=7, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_det.bind("<Enter>", (lambda event: self.show_tooltip("With dynamic_energy_threshold set to 'Yes', \nthe program will continuously try to re-adjust the energy threshold\n to match the environment based on the ambient noise level at that time.\nI'd recommend setting the 'energy_threshold' value \nhigh when enabling this setting.")))
        self.label_det.bind("<Leave>", self.hide_tooltip)

        self.label_energy_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Energy Threshold', font=(self.FONT, 12))
        self.label_energy_threshold.grid(row=8, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_energy_threshold = tk.Entry(self.tkui)
        self.entry_energy_threshold.insert(0, self.config["energy_threshold"])
        self.entry_energy_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_energy_threshold.grid(row=8, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_energy_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Under 'ideal' conditions (such as in a quiet room), \nvalues between 0 and 100 are considered silent or ambient,\n and values 300 to about 3500 are considered speech.")))
        self.label_energy_threshold.bind("<Leave>", self.hide_tooltip)
        self.button_refresh = tk.Button(self.tkui, text="⭯")
        self.button_refresh.configure(bg="#333333", fg="white", highlightthickness=0, anchor="center", activebackground="#555555", activeforeground="white")
        self.button_refresh.grid(row=8, column=2, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_pause_threshold = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Pause Threshold', font=(self.FONT, 12))
        self.label_pause_threshold.grid(row=9, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_pause_threshold = tk.Entry(self.tkui)
        self.entry_pause_threshold.insert(0, self.config["pause_threshold"])
        self.entry_pause_threshold.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_pause_threshold.grid(row=9, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_pause_threshold.bind("<Enter>", (lambda event: self.show_tooltip("Amount of seconds to wait when current energy is under the 'energy_threshold'.")))
        self.label_pause_threshold.bind("<Leave>", self.hide_tooltip)

        self.label_timeout_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Timeout Time', font=(self.FONT, 12))
        self.label_timeout_time.grid(row=10, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_timeout_time = tk.Entry(self.tkui)
        self.entry_timeout_time.insert(0, self.config["timeout_time"])
        self.entry_timeout_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_timeout_time.grid(row=10, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_timeout_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to wait for the user to speak before timeout.")))
        self.label_timeout_time.bind("<Leave>", self.hide_tooltip)

        self.label_hold_time = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Hold Time', font=(self.FONT, 12))
        self.label_hold_time.grid(row=11, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_hold_time = tk.Entry(self.tkui)
        self.entry_hold_time.insert(0, self.config["hold_time"])
        self.entry_hold_time.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_hold_time.grid(row=11, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_hold_time.bind("<Enter>", (lambda event: self.show_tooltip("Amount of time to hold the button to clear the Textbox.")))
        self.label_hold_time.bind("<Leave>", self.hide_tooltip)

        self.label_phrase_time_limit = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Phrase time limit', font=(self.FONT, 12))
        self.label_phrase_time_limit.grid(row=12, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_phrase_time_limit = tk.Entry(self.tkui)
        self.entry_phrase_time_limit.insert(0, self.config["phrase_time_limit"])
        self.entry_phrase_time_limit.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_phrase_time_limit.grid(row=12, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_phrase_time_limit.bind("<Enter>", (lambda event: self.show_tooltip("The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached")))
        self.label_phrase_time_limit.bind("<Leave>", self.hide_tooltip)

        self.label_mic = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Microphone', font=(self.FONT, 12))
        self.label_mic.grid(row=13, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.option_index = 0 if self.config["microphone_index"] is None else int(self.config["microphone_index"]) + 1
        self.options_mic = self.get_sound_devices()
        self.value_mic = tk.StringVar(self.tkui)
        self.value_mic.set(self.options_mic[self.option_index])
        self.opt_mic = tk.OptionMenu(self.tkui, self.value_mic, *self.options_mic)
        self.opt_mic.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_mic.grid(row=13, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_mic.bind("<Enter>", (lambda event: self.show_tooltip("What microphone to use. 'Default' will use your systems default microphone.")))
        self.label_mic.bind("<Leave>", self.hide_tooltip)

        self.label_banned_words = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Banned Words', font=(self.FONT, 12))
        self.label_banned_words.grid(row=14, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_banned_words = tk.Entry(self.tkui)
        if self.config["banned_words"] is not None:
            self.entry_banned_words.insert(0, ','.join(self.config["banned_words"]))
        self.entry_banned_words.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_banned_words.grid(row=14, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_banned_words.bind("<Enter>", (lambda event: self.show_tooltip("List of Banned words that are gonna get removed from the transcribed text. seperated by comma ','")))
        self.label_banned_words.bind("<Leave>", self.hide_tooltip)

        self.label_use_textbox = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Textbox', font=(self.FONT, 12))
        self.label_use_textbox.grid(row=15, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_use_textbox = tk.StringVar(self.tkui)
        self.value_use_textbox.set("yes" if bool(self.config["use_textbox"]) else "no")
        self.opt_use_textbox = tk.OptionMenu(self.tkui, self.value_use_textbox, *self.yn_options)
        self.opt_use_textbox.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_textbox.grid(row=15, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_use_textbox.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to VRChats Textbox")))
        self.label_use_textbox.bind("<Leave>", self.hide_tooltip)
        self.value_use_textbox.trace_add("write", (lambda *args: self.changed()))

        self.label_use_kat = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use KAT', font=(self.FONT, 12))
        self.label_use_kat.grid(row=16, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_use_kat = tk.StringVar(self.tkui)
        self.value_use_kat.set("yes" if bool(self.config["use_kat"]) else "no")
        self.opt_use_kat = tk.OptionMenu(self.tkui, self.value_use_kat, *self.yn_options)
        self.opt_use_kat.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_kat.grid(row=16, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_use_kat.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to KillFrenzyAvatarText")))
        self.label_use_kat.bind("<Leave>", self.hide_tooltip)
        self.value_use_kat.trace_add("write", (lambda *args: self.changed()))

        self.label_use_both = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Use Both', font=(self.FONT, 12))
        self.label_use_both.grid(row=17, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.value_use_both = tk.StringVar(self.tkui)
        self.value_use_both.set("yes" if bool(self.config["use_both"]) else "no")
        self.opt_use_both = tk.OptionMenu(self.tkui, self.value_use_both, *self.yn_options)
        self.opt_use_both.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.opt_use_both.grid(row=17, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_use_both.bind("<Enter>", (lambda event: self.show_tooltip("If you want to send your text to both options above, if both available and set to 'Yes'.\nIf not, the program will prefer sending to KillFrenzyAvatarText if it is available.")))
        self.label_use_both.bind("<Leave>", self.hide_tooltip)

        self.label_emotes = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emotes', font=(self.FONT, 12))
        self.label_emotes.grid(row=18, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.button_emotes = tk.Button(self.tkui, text="Edit Emotes", command=self.button_hotkey_pressed)
        self.button_emotes.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, width=23, anchor="center", activebackground="#555555", activeforeground="white", command=self.open_emote_window)
        self.button_emotes.grid(row=18, column=1, padx=PADX_R, pady=PADY, sticky='ws')
        self.label_emotes.bind("<Enter>", (lambda event: self.show_tooltip("The key that is used to trigger listening.\nKlick on the button and press the button you want to use.")))
        self.label_emotes.bind("<Leave>", self.hide_tooltip)

        self.btn_save = tk.Button(self.tkui, text="Save")
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=53, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.96, anchor="center")

    def open_emote_window(self):
        self.ew = EmoteWindow(self.config, self.config_path)
        self.ew.btn_save.configure(command=self.emote_window_save)
    
    def emote_window_save(self):
        self.config["emotes"]["0"] = self.ew.entry_one.get()
        self.config["emotes"]["1"] = self.ew.entry_two.get()
        self.config["emotes"]["2"] = self.ew.entry_three.get()
        self.config["emotes"]["3"] = self.ew.entry_four.get()
        self.config["emotes"]["4"] = self.ew.entry_five.get()
        self.config["emotes"]["5"] = self.ew.entry_six.get()
        self.config["emotes"]["6"] = self.ew.entry_seven.get()
        self.config["emotes"]["7"] = self.ew.entry_eight.get()
        self.config["emotes"]["8"] = self.ew.entry_nine.get()
        self.config["emotes"]["9"] = self.ew.entry_ten.get()
        self.config["emotes"]["10"] = self.ew.entry_eleven.get()
        self.config["emotes"]["11"] = self.ew.entry_twelve.get()
        self.config["emotes"]["12"] = self.ew.entry_thirteen.get()
        self.config["emotes"]["13"] = self.ew.entry_fourteen.get()
        self.config["emotes"]["14"] = self.ew.entry_fifteen.get()
        json.dump(self.config, open(self.config_path, "w"), indent=4)
        self.ew.on_closing()

    def get_sound_devices(self):
        res = ["Default"]
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdev = info.get("deviceCount")

        for i in range(0, numdev):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                res.append([i, p.get_device_info_by_host_api_device_index(0, i).get('name')])

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
            return None
        else:
            return res.split(',')

    def save(self):
        self.config["osc_ip"] = self.entry_osc_ip.get()
        self.config["osc_port"] = int(self.entry_osc_port.get())
        self.config["osc_server_port"] = int(self.entry_osc_server_port.get())
        self.config["model"] = self.value_model.get()
        self.config["language"] = self.value_language.get()
        self.config["hotkey"] = self.set_key
        self.config["continuous"] = True if self.value_continuous.get() == "continuous" else False
        self.config["dynamic_energy_threshold"] = True if self.value_det.get() == "yes" else False
        self.config["energy_threshold"] = int(self.entry_energy_threshold.get())
        self.config["pause_threshold"] = float(self.entry_pause_threshold.get())
        self.config["timeout_time"] = float(self.entry_timeout_time.get())
        self.config["hold_time"] = float(self.entry_hold_time.get())
        self.config["phrase_time_limit"] = float(self.entry_phrase_time_limit.get())
        self.config["microphone_index"] = self.get_audiodevice_index()
        self.config["banned_words"] = self.get_banned_words()
        self.config["use_textbox"] = True if self.value_use_textbox.get() == "yes" else False
        self.config["use_kat"] = True if self.value_use_kat.get() == "yes" else False
        self.config["use_both"] = True if self.value_use_both.get() == "yes" else False

        json.dump(self.config, open(self.config_path, "w"), indent=4)

    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def open(self):
        print("OPEN SETTINGS")
        self.tkui.mainloop()

    def on_closing(self):
        self.closed = True
        self.tkui.destroy()

    def button_hotkey_pressed(self):
        self.button_hotkey.configure(text="Press a button\nor ESC to cancel...", state="disabled", disabledforeground="white", height=2, width=37, font=(self.FONT, 7))
        self.update()
        key = keyboard.read_key()
        if key != "esc":
            self.set_key = key
        self.button_hotkey.configure(text=self.config["hotkey"], state="normal")
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
        self.tooltip_window.destroy()
        self.tooltip_window = None

    def changed(self):
        if self.value_use_kat.get() == "no" or self.value_use_textbox.get() == "no":
            self.opt_use_both.configure(state="disabled")
        else:
            self.opt_use_both.configure(state="normal")

    def set_energy_threshold(self, text):
        self.entry_energy_threshold.delete(0, tk.END)
        self.entry_energy_threshold.insert(0, str(text))
        self.update()

class EmoteWindow:
    def __init__(self, config, config_path):
        self.config = config
        self.config_path = config_path
        self.FONT = "Cascadia Code"

        PADX_R = '0'
        PADX_L = '30'
        PADY = '4'

        self.tkui = tk.Tk()
        self.tkui.minsize(350, 570)
        self.tkui.maxsize(350, 570)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT - Emotes")

        self.label_one = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 1', font=(self.FONT, 12))
        self.label_one.grid(row=0, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_one = tk.Entry(self.tkui)
        self.entry_one.insert(0, self.config["emotes"]["0"])
        self.entry_one.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_one.grid(row=0, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_two = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 2', font=(self.FONT, 12))
        self.label_two.grid(row=1, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_two = tk.Entry(self.tkui)
        self.entry_two.insert(0, self.config["emotes"]["1"])
        self.entry_two.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_two.grid(row=1, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_three = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 3', font=(self.FONT, 12))
        self.label_three.grid(row=2, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_three = tk.Entry(self.tkui)
        self.entry_three.insert(0, self.config["emotes"]["2"])
        self.entry_three.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_three.grid(row=2, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_four = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 4', font=(self.FONT, 12))
        self.label_four.grid(row=3, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_four = tk.Entry(self.tkui)
        self.entry_four.insert(0, self.config["emotes"]["3"])
        self.entry_four.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_four.grid(row=3, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_five = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 5', font=(self.FONT, 12))
        self.label_five.grid(row=4, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_five = tk.Entry(self.tkui)
        self.entry_five.insert(0, self.config["emotes"]["4"])
        self.entry_five.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_five.grid(row=4, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_six = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 6', font=(self.FONT, 12))
        self.label_six.grid(row=5, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_six = tk.Entry(self.tkui)
        self.entry_six.insert(0, self.config["emotes"]["5"])
        self.entry_six.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_six.grid(row=5, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_seven = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 7', font=(self.FONT, 12))
        self.label_seven.grid(row=6, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_seven = tk.Entry(self.tkui)
        self.entry_seven.insert(0, self.config["emotes"]["6"])
        self.entry_seven.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_seven.grid(row=6, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_eight = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 8', font=(self.FONT, 12))
        self.label_eight.grid(row=7, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_eight = tk.Entry(self.tkui)
        self.entry_eight.insert(0, self.config["emotes"]["7"])
        self.entry_eight.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_eight.grid(row=7, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_nine = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 9', font=(self.FONT, 12))
        self.label_nine.grid(row=8, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_nine = tk.Entry(self.tkui)
        self.entry_nine.insert(0, self.config["emotes"]["8"])
        self.entry_nine.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_nine.grid(row=8, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_ten = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 10', font=(self.FONT, 12))
        self.label_ten.grid(row=9, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_ten = tk.Entry(self.tkui)
        self.entry_ten.insert(0, self.config["emotes"]["9"])
        self.entry_ten.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_ten.grid(row=9, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_eleven = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 11', font=(self.FONT, 12))
        self.label_eleven.grid(row=10, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_eleven = tk.Entry(self.tkui)
        self.entry_eleven.insert(0, self.config["emotes"]["10"])
        self.entry_eleven.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_eleven.grid(row=10, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_twelve = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 12', font=(self.FONT, 12))
        self.label_twelve.grid(row=11, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_twelve = tk.Entry(self.tkui)
        self.entry_twelve.insert(0, self.config["emotes"]["11"])
        self.entry_twelve.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_twelve.grid(row=11, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_thirteen = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 13', font=(self.FONT, 12))
        self.label_thirteen.grid(row=12, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_thirteen = tk.Entry(self.tkui)
        self.entry_thirteen.insert(0, self.config["emotes"]["12"])
        self.entry_thirteen.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_thirteen.grid(row=12, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_fourteen = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 14', font=(self.FONT, 12))
        self.label_fourteen.grid(row=13, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_fourteen = tk.Entry(self.tkui)
        self.entry_fourteen.insert(0, self.config["emotes"]["13"])
        self.entry_fourteen.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_fourteen.grid(row=13, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.label_fifteen = tk.Label(master=self.tkui, bg="#333333", fg="white", text='Emote 15', font=(self.FONT, 12))
        self.label_fifteen.grid(row=14, column=0, padx=PADX_L, pady=PADY, sticky='es')
        self.entry_fifteen = tk.Entry(self.tkui)
        self.entry_fifteen.insert(0, self.config["emotes"]["14"])
        self.entry_fifteen.configure(bg="#333333", fg="white", font=(self.FONT, 10), highlightthickness=0, insertbackground="#666666", width=23)
        self.entry_fifteen.grid(row=14, column=1, padx=PADX_R, pady=PADY, sticky='ws')

        self.btn_save = tk.Button(self.tkui, text="Save")
        self.btn_save.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=33, anchor="center", highlightthickness=0, activebackground="#555555", activeforeground="white")
        self.btn_save.place(relx=0.5, rely=0.96, anchor="center")

    def on_closing(self):
        self.tkui.destroy()