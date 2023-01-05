import tkinter as tk

class UI(object):

    def __init__(self):
        self.ui = tk.Tk()
        self.ui.minsize(810, 310)
        self.ui.maxsize(810, 310)
        self.ui.resizable(False, False)
        self.ui.configure(bg="#333333")
        self.ui.title("TextboxSTT")

        self.status_lbl = tk.Label(self.ui, text="INITIALIZING")
        self.status_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 12))
        self.status_lbl.place(relx=0.047, rely=0.065, anchor="w")

        self.color_lbl = tk.Label(self.ui, text="")
        self.color_lbl.configure(bg="red", width=2, fg="white", font=("Cascadia Code", 12))
        self.color_lbl.place(relx=0.01, rely=0.07, anchor="w")

        self.text_lbl = tk.Label(self.ui, wraplength=800, text="- No Text -")
        self.text_lbl.configure(bg="#333333", fg="white", font=("Cascadia Code", 27))
        self.text_lbl.place(relx=0.5, rely=0.55, anchor="center")
        self.update()
    
    def update(self):
        self.ui.update()
        self.ui.update_idletasks()

    def set_status_label(self, text, color):
        self.status_lbl.configure(text=text)
        self.color_lbl.configure(bg=color)
        self.update()
        print(text)

    def set_text_label(self, text):
        self.text_lbl.configure(text=text)
        self.update()
