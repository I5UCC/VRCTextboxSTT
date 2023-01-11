import tkinter as tk


class UI(object):
    def __init__(self, version, ip, port, options, option_index):
        option_index = 0 if option_index is None else int(option_index) + 1

        FONT = "Cascadia Code"
        self.version = version
        self.options = options
        print(version)

        self.tkui = tk.Tk()
        self.tkui.minsize(810, 350)
        self.tkui.maxsize(810, 350)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT")

        self.text_lbl = tk.Label(self.tkui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=(FONT, 27))
        self.text_lbl.place(relx=0.5, rely=0.53, anchor="center")

        self.conf_lbl = tk.Label(self.tkui, text=f"OSC: {ip}:{port}, OVR: Connecting")
        self.conf_lbl.configure(bg="#333333", fg="#666666", font=(FONT, 10))
        self.conf_lbl.place(relx=0.01, rely=0.935, anchor="w")

        self.ver_lbl = tk.Label(self.tkui, text=self.version)
        self.ver_lbl.configure(bg="#333333", fg="#666666", font=(FONT, 10))
        self.ver_lbl.place(relx=0.99, rely=0.05, anchor="e")

        self.status_lbl = tk.Label(self.tkui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=(FONT, 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.tkui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=(FONT, 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.options_lbl = tk.Label(self.tkui, text="Microphone:")
        self.options_lbl.configure(bg="#333333", fg="#666666", font=(FONT, 12))
        self.options_lbl.place(relx=0.72, rely=0.93, anchor="e")

        self.value_inside = tk.StringVar(self.tkui)
        self.value_inside.set(self.options[option_index])
        self.mic_opt = tk.OptionMenu(self.tkui, self.value_inside, *self.options)
        self.mic_opt.configure(bg="#333333", fg="white", font=(FONT, 10), width=25, anchor="w", highlightthickness=0, activebackground="#555555", activeforeground="white", indicatoron=0)
        self.mic_opt.place(relx=0.99, rely=0.93, anchor="e")
        self.update()

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
    
    def loading_status(self, s:str):
        try:
            self.set_text_label(f"Downloading Model:{s[s.rindex('|')+1:]}")
        except Exception:
            self.set_text_label("Done.")

    def set_conf_label(self, ip, port, ovr_initialized=False):
        self.ver_lbl.configure(text=self.version)
        self.conf_lbl.configure(text=f"OSC: {ip}:{port}, OVR: {'Connected' if ovr_initialized else 'Failed to Connect'}")
        self.update()
