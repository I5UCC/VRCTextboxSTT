import tkinter as tk
from config import config_struct
from helper import get_absolute_path

class Configurator(tk.Tk):
    def __init__(self, config: config_struct, config_path: str):
        super().__init__()
        self.title("Configurator")
        self.geometry("400x300")
        self.minsize(400, 300)
        self.maxsize(400, 300)
        self.configure(bg="#333333")
        self.FONT = "Cascadia Code"
        self.config = config
        self.config_path = config_path

        self.pages = []
        self.current_page = 0

        button_skip = tk.Button(self, text="Skip", command=self.next_page, bg="#333333", fg="white", font=(self.FONT, 10))
        button_skip.place(x=350, y=260)

        self.create_pages()
        self.show_current_page()

    def create_pages(self):
        page1 = tk.Frame(self, bg="#333333", width=400, height=300)
        page1_label = tk.Label(page1, text="Page 1", bg="#333333", fg="white", font=(self.FONT, 14))
        page1_label.pack(padx=10, pady=10)

        def use_kat():
            self.config.osc.use_kat = True
            self.config.osc.use_textbox = False
            self.config.osc.use_both = False
            self.next_page()
        button_KAT = tk.Button(page1, text="USE KAT", command=use_kat, bg="#333333", fg="white", font=(self.FONT, 12), width=20, height=1)
        button_KAT.pack(padx=10, pady=10)
        def use_textbox():
            self.config.osc.use_kat = False
            self.config.osc.use_textbox = True
            self.config.osc.use_both = False
            self.next_page()
        button_textbox = tk.Button(page1, text="USE TEXTBOX", command=use_textbox, bg="#333333", fg="white", font=(self.FONT, 12), width=20, height=1)
        button_textbox.pack(padx=10, pady=10)
        def use_both():
            self.config.osc.use_kat = True
            self.config.osc.use_textbox = True
            self.config.osc.use_both = True
            self.next_page()
        button_both = tk.Button(page1, text="USE BOTH", command=use_both, bg="#333333", fg="white", font=(self.FONT, 12), width=20, height=1)
        button_both.pack(padx=10, pady=10)
        self.pages.append(page1)

        page2 = tk.Frame(self, bg="#333333")
        page2_label = tk.Label(page2, text="Page 2", bg="#333333", fg="white")
        page2_label.pack()
        self.pages.append(page2)

        page3 = tk.Frame(self, bg="#333333")
        page3_label = tk.Label(page3, text="Page 3", bg="#333333", fg="white")
        page3_label.pack()
        self.pages.append(page3)

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