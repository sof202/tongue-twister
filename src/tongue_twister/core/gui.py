from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core.audio_manager import AudioManager
from core.tongue_twister_manager import TongueTwistersManager


class App(tk.Tk):
    def __init__(
        self,
        audio_manager: AudioManager,
        tongue_twister_manager: TongueTwistersManager,
    ) -> None:
        super().__init__()
        self.audio_manager = audio_manager
        self.tongue_twister_manager = tongue_twister_manager
        self.title("Tongue Twisters")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.set_styles()
        self.help_message = (
            "HELP\n"
            "1) Press next to get a new tongue twister.\n\n"
            "2) Press start/stop to begin delayed audio feedback and try to "
            "say the tongue twister.\n\n"
            "3) Press start/stop again to end the delayed audio feedback."
        )
        self.create_widgets()
        self.create_keybinds()

    def set_styles(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.bg_colour = "#1e1e1e"
        self.text_colour = "#ffffff"
        self.button_colour = "#333333"
        self.button_hover_colour = "#444444"
        self.button_active_colour = "#555555"
        self.exit_button_colour = "#5c1e1e"

        self.configure(background=self.bg_colour)

        self.style.configure(
            "Main.TLabel",
            font=("Segoe UI", 40),
            background=self.bg_colour,
            foreground=self.text_colour,
            anchor="center",
            padding=0,
        )

        self.style.configure("ButtonFrame.TFrame", background=self.bg_colour)

        self.style.configure(
            "TButton",
            font=("Segoe UI", 24),
            padding=10,
            relief="flat",
            cursor="hand2",
        )

        self.style.configure(
            "Dark.TButton",
            background=self.button_colour,
            foreground=self.text_colour,
        )

        self.style.configure(
            "Exit.TButton",
            background=self.exit_button_colour,
            foreground=self.text_colour,
        )

        self.style.map(
            "TButton",
            foreground=[
                ("pressed", self.text_colour),
                ("active", self.text_colour),
            ],
            background=[
                ("pressed", self.button_active_colour),
                ("active", self.button_hover_colour),
            ],
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def create_widgets(self) -> None:
        self.text_box = ttk.Label(
            self,
            text=self.help_message,
            style="Main.TLabel",
            wraplength=self.winfo_screenwidth() - 300,
            justify=tk.CENTER,
        )
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)

        button_frame = ttk.Frame(self, style="ButtonFrame.TFrame")
        button_frame.grid(row=1, column=0, sticky="s", pady=(0, 20))

        self.start_stop_button = ttk.Button(
            button_frame,
            text="Start/Stop ⏯",
            style="Dark.TButton",
            command=self.start_stop_clicked,
        )
        self.start_stop_button.pack(side="left", padx=10)

        self.next_button = ttk.Button(
            button_frame,
            text="Next ⏭",
            style="Dark.TButton",
            command=self.get_new_tongue_twister,
        )
        self.next_button.pack(side="left", padx=10)

        self.exit_button = ttk.Button(
            self,
            text="✕",
            style="Exit.TButton",
            command=self.quit_app,
            width=3,
        )
        self.exit_button.place(relx=0.99, rely=0.01, anchor="ne")

        self.help_button = ttk.Button(
            self,
            text="?",
            style="Dark.TButton",
            command=self.set_help,
            width=3,
        )
        self.help_button.place(relx=0.01, rely=0.01, anchor="nw")

    def create_keybinds(self) -> None:
        self.bind("n", self.get_new_tongue_twister)
        self.bind("<space>", self.start_stop_clicked)
        self.bind("h", self.set_help)
        self.bind("q", self.quit_app)

    def set_help(self, event: tk.Event = None) -> None:
        self.text_box.config(text=self.help_message)

    def get_new_tongue_twister(self, event: tk.Event = None) -> None:
        self.text_box.config(
            text=self.tongue_twister_manager.get_next_tongue_twister()
        )

    def start_stop_clicked(self, event: tk.Event = None) -> None:
        if self.audio_manager.running:
            self.audio_manager.stop()
        else:
            self.audio_manager.start()

    def quit_app(self, event: tk.Event = None) -> None:
        self.audio_manager.stop()
        self.destroy()
