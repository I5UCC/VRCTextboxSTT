import tkinter as tk

class UI(object):

    def __init__(self):
        self.tkui = tk.Tk()
        self.tkui.minsize(810, 310)
        self.tkui.maxsize(810, 310)
        self.tkui.resizable(False, False)
        self.tkui.configure(bg="#333333")
        self.tkui.title("TextboxSTT")

        self.conf_lbl = tk.Label(self.tkui, text="IP:PORT")
        self.conf_lbl.configure(bg="#333333", fg="#666666", font=("Cascadia Code", 10))
        self.conf_lbl.place(relx=0.99, rely=0.05, anchor="e")

        self.status_lbl = tk.Label(self.tkui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.tkui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=("Cascadia Code", 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.text_lbl = tk.Label(self.tkui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 27))
        self.text_lbl.place(relx=0.5, rely=0.55, anchor="center")
        self.update()
    
    def update(self):
        self.tkui.update()
        self.tkui.update_idletasks()

    def set_status_label(self, text, color):
        self.status_lbl.configure(text=text)
        self.color_lbl.configure(bg=color)
        self.update()
        print(text)

    def set_text_label(self, text):
        self.text_lbl.configure(text=text)
        self.update()

    def set_conf_label(self, ip, port):
        self.conf_lbl.configure(text=f"{ip}:{port}")
        self.update()
