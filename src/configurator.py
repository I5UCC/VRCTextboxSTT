import tkinter as tk
from listen import ListenHandler
from config import config_struct, WHISPER_MODELS
from ui import SettingsWindow
from helper import get_absolute_path
import torch

class Configurator(tk.Tk):
    def __init__(self, config: config_struct, config_path: str):
        super().__init__()
        self.title("Configurator")
        self.geometry("450x440")
        self.minsize(450, 460)
        self.maxsize(450, 460)
        self.configure(bg="#333333")
        self.FONT = "Cascadia Code"
        self.config = config
        self.config_path = config_path

        self.pages = []
        self.current_page = 0

        button_skip = tk.Button(self, text="Skip", command=self.next_page, bg="#333333", fg="white", font=(self.FONT, 10))
        button_skip.place(x=400, y=420)

        button_back = tk.Button(self, text="Back", command=self.previous_page, bg="#333333", fg="white", font=(self.FONT, 10))
        button_back.place(x=10, y=420)

        self.create_pages()
        self.show_current_page()

    def page_output(self):
        page = tk.Frame(self, bg="#333333", width=400, height=300)
        label_top = tk.Label(page, text="What Output Method do you want to use?", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 14))
        label_top.pack(padx=0, pady=10)
        label2 = tk.Label(page, text="If you dont know what KAT is, you want to use VRChats Textbox.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label2.pack(padx=0, pady=30)
        def use_textbox():
            self.config.osc.use_kat = False
            self.config.osc.use_textbox = True
            self.config.osc.use_both = False
            self.config.osc.server_port = -1
            self.config.emotes.enabled = False
            self.next_page()
        button_textbox = tk.Button(page, text="Use VRChat Textbox", command=use_textbox, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_textbox.pack(padx=0, pady=10)
        def use_kat():
            self.config.osc.use_kat = True
            self.config.osc.use_textbox = False
            self.config.osc.use_both = False
            self.config.osc.server_port = 9000
            self.config.emotes.enabled = True
            self.next_page()
        button_KAT = tk.Button(page, text="Use KAT", command=use_kat, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_KAT.pack(padx=0, pady=10)
        def use_both():
            self.config.osc.use_kat = True
            self.config.osc.use_textbox = True
            self.config.osc.use_both = True
            self.config.osc.server_port = 9000
            self.config.emotes.enabled = True
            self.next_page()
        button_both = tk.Button(page, text="Use Both (Auto Detect)", command=use_both, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_both.pack(padx=0, pady=10)
        return page

    def page_mode(self):
        page = tk.Frame(self, bg="#333333")
        label_top = tk.Label(page, text="What Transcription mode do you want to use?", wraplength=440, bg="#333333", fg="white", font=(self.FONT, 14))
        label_top.pack(padx=0, pady=10)
        def once_continous():
            self.config.mode = 1
            self.next_page()
        button_once_continous = tk.Button(page, text="once_continous", command=once_continous, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_once_continous.pack(padx=10, pady=10)
        label2 = tk.Label(page, text="(Recommended) Listen Once, output interim results while talking.", wraplength=440, bg="#333333", fg="white", font=(self.FONT, 10))
        label2.pack(padx=0, pady=0)
        def once():
            self.config.mode = 0
            self.next_page()
        button_once = tk.Button(page, text="once", command=once, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_once.pack(padx=0, pady=10)
        label3 = tk.Label(page, text="Listen Once, Trascribe after", wraplength=440, bg="#333333", fg="white", font=(self.FONT, 10))
        label3.pack(padx=0, pady=0)
        def realtime():
            self.config.mode = 2
            self.next_page()
        button_realtime = tk.Button(page, text="realtime", command=realtime, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_realtime.pack(padx=0, pady=10)
        label4 = tk.Label(page, text="Continously listen and output results whenever needed.", wraplength=440, bg="#333333", fg="white", font=(self.FONT, 10))
        label4.pack(padx=0, pady=0)
        return page

    def page_mic(self):
        page = tk.Frame(self, bg="#333333")
        label_top = tk.Label(page, text="Set Microphone and Energy Threshold", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 14))
        label_top.pack(padx=0, pady=10)
        label2 = tk.Label(page, text="Microphone", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label2.pack(padx=0, pady=0)
        value_mic = tk.StringVar(page)
        options_mic = SettingsWindow.get_sound_devices(None)
        value_mic.set("Default")
        opt_mic = tk.OptionMenu(page, value_mic, *options_mic)
        opt_mic.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=19, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        opt_mic.pack(padx=0, pady=0)
        label3 = tk.Label(page, text="Energy Threshold", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label3.pack(padx=0, pady=0)
        label5 = tk.Label(page, text="Energy Threshold is the minimum energy level that the microphone needs to detect to start listening. Under 'ideal' conditions (such as in a quiet room), values between 0 and 100 are considered silent or ambient, and values 300 to about 3500 are considered speech.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label5.pack(padx=0, pady=0)
        def get_energy():
            button_refresh.config(state="disabled", text="Be silent for 5 seconds...", width=30)
            self.update()
            option = value_mic.get()
            tmp = None
            if option != "Default":
                tmp = int(option[1:option.index(',')])
            self.config.listener.microphone_index = tmp
            listener = ListenHandler(self.config.listener)
            listener.config.energy_threshold = listener.get_energy_threshold()
            entry_energy.delete(0, tk.END)
            entry_energy.insert(0, listener.config.energy_threshold)
            button_refresh.config(state="normal", text="Refresh", width=20)
            self.update()
        button_refresh = tk.Button(page, text="Refresh", command=get_energy, bg="#333333", fg="white", font=(self.FONT, 10), width=20, height=1)
        button_refresh.pack(padx=0, pady=10)
        value_energy = tk.StringVar(page)
        value_energy.set("200")
        entry_energy = tk.Entry(page, textvariable=value_energy, bg="#333333", fg="white", font=(self.FONT, 10), width=20)
        entry_energy.pack(padx=0, pady=0)
        label4 = tk.Label(page, text="Click Refresh to get the energy threshold of your microphone. Be silent for 5 seconds after pressing the button.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label4.pack(padx=0, pady=0)
        def save():
            self.config.listener.energy_threshold = int(entry_energy.get())
            option = value_mic.get()
            tmp = None
            if option != "Default":
                tmp = int(option[1:option.index(',')])
            self.config.listener.microphone_index = tmp
            self.next_page()
        button_next = tk.Button(page, text="Save", command=save, bg="#333333", fg="white", font=(self.FONT, 10), width=20, height=1)
        button_next.pack(padx=0, pady=10)
        return page

    def page_overlay(self):
        page = tk.Frame(self, bg="#333333")
        label_top = tk.Label(page, text="Use SteamVR Overlay?", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 14))
        label_top.pack(padx=0, pady=10)
        label2 = tk.Label(page, text="Use the SteamVR Overlay to display the transcription.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label2.pack(padx=0, pady=30)
        def overlay_yes():
            self.config.overlay.enabled = True
            self.next_page()
        button_yes = tk.Button(page, text="Yes", command=overlay_yes, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_yes.pack(padx=0, pady=10)
        def overlay_no():
            self.config.overlay.enabled = False
            self.next_page()
        button_no = tk.Button(page, text="No", command=overlay_no, bg="#333333", fg="white", font=(self.FONT, 12), width=30, height=1)
        button_no.pack(padx=0, pady=10)
        return page
    
    def page_device_model(self):
        page = tk.Frame(self, bg="#333333")
        label_top = tk.Label(page, text="Select the device you want to use", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 14))
        label_top.pack(padx=0, pady=10)
        label2 = tk.Label(page, text="Select the device you want to use for the transcription.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label2.pack(padx=0, pady=0)
        devices_list = []
        if torch.cuda.is_available():
            for i in range(0, torch.cuda.device_count()):
                devices_list.append((i, torch.cuda.get_device_name(i)))
            
        devices_list.append("CPU")
        value_device = tk.StringVar(page)
        value_device.set(devices_list[0])
        opt_device = tk.OptionMenu(page, value_device, *devices_list)
        opt_device.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=30, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        opt_device.pack(padx=0, pady=35)

        label3 = tk.Label(page, text="Select the model you want to use for the transcription. read the #Requirements for more information.", wraplength=420, bg="#333333", fg="white", font=(self.FONT, 10))
        label3.pack(padx=0, pady=0)

        value_model = tk.StringVar(page)
        models = []
        for key in WHISPER_MODELS:
            if ".en" not in key:
                models.append(key)
        if self.config.whisper.custom_models:
            models = models + self.config.whisper.custom_models
        value_model.set("distil-small")
        opt_model = tk.OptionMenu(page, value_model, *models)
        opt_model.configure(bg="#333333", fg="white", font=(self.FONT, 10), width=30, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white")
        opt_model.pack(padx=0, pady=35)

        def save():
            self.config.whisper.device.type = "cuda" if torch.cuda.is_available() and value_device.get().lower() != "cpu" else "cpu"
            self.config.whisper.device.index = int(value_device.get()[1]) if torch.cuda.is_available() and value_device.get().lower() != "cpu" else 0
            self.config.whisper.model = value_model.get()
            self.next_page()
        button_next = tk.Button(page, text="Save", command=save, bg="#333333", fg="white", font=(self.FONT, 10), width=20, height=1)
        button_next.pack(padx=0, pady=10)
        return page

    def create_pages(self):
        self.pages.append(self.page_output())
        self.pages.append(self.page_mode())
        self.pages.append(self.page_mic())
        self.pages.append(self.page_overlay())
        self.pages.append(self.page_device_model())

    def show_current_page(self):
        current_page = self.pages[self.current_page]
        current_page.pack()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.pages[self.current_page].pack_forget()
            self.current_page += 1
            self.show_current_page()
        else:
            self.end_configurator()

    def previous_page(self):
        if self.current_page > 0:
            self.pages[self.current_page].pack_forget()
            self.current_page -= 1
            self.show_current_page()
    
    def end_configurator(self):
        config_struct.save(self.config, self.config_path)
        self.destroy()

if __name__ == "__main__":
    config_path = get_absolute_path("../configs/default.json")
    print(config_path)
    config = config_struct.load(config_path)
    configurator = Configurator(config, config_path)
    configurator.mainloop()