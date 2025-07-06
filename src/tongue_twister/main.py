from __future__ import annotations

import asyncio
import importlib.resources
import threading
import time
import tkinter as tk
from argparse import Namespace
from random import shuffle
from tkinter import ttk
from types import TracebackType
from typing import Optional, Type

import pyaudio

FORMAT = pyaudio.paInt16
CHUNK = 1024
RATE = 44100
CHANNELS = 1
EPSILON = 1e-8


class TongueTwistersManager:
    def __init__(self, file: str) -> None:
        self.file = file
        self.tongue_twisters = []
        self.current_index = 0
        self.load_tongue_twisters()
        self.shuffle_tongue_twisters()

    def load_tongue_twisters(self) -> list[str]:
        with importlib.resources.open_text("data", self.file) as file:
            for line in file.readlines():
                self.tongue_twisters.append(line.strip())

    def shuffle_tongue_twisters(self) -> None:
        shuffle(self.tongue_twisters)

    def get_next_tongue_twister(self) -> str:
        if len(self.tongue_twisters) == 0:
            # TODO: add custom exception
            print("No tongue twisters loaded")
        if len(self.tongue_twisters) <= self.current_index:
            self.current_index = 0
        tongue_twister = self.tongue_twisters[self.current_index]
        self.current_index += 1
        return tongue_twister


def print_available_audio_devices() -> None:
    audio = pyaudio.PyAudio()
    info = audio.get_host_api_info_by_index(0)
    number_of_devices = info.get("deviceCount")
    print("--input devices-------------------------------------------------")
    for i in range(number_of_devices):
        if (
            audio.get_device_info_by_host_api_device_index(0, i).get(
                "maxInputChannels"
            )
            > 0
        ):
            print(
                "  ",
                i,
                "-",
                audio.get_device_info_by_host_api_device_index(0, i).get(
                    "name"
                ),
            )
    print("--output devices------------------------------------------------")
    for i in range(number_of_devices):
        if (
            audio.get_device_info_by_host_api_device_index(0, i).get(
                "maxOutputChannels"
            )
            > 0
        ):
            print(
                "  ",
                i,
                "-",
                audio.get_device_info_by_host_api_device_index(0, i).get(
                    "name"
                ),
            )

    print("----------------------------------------------------------------")


class AudioManager:
    def __init__(
        self, input_device: int, output_device: int, delay_seconds: float
    ) -> None:
        self.audio = pyaudio.PyAudio()
        self.running = False
        self.loop = None
        self.queue = None
        self.thread = None
        self.input_device = input_device
        self.output_device = output_device
        self.delay_seconds = delay_seconds

    def start(self) -> None:
        if not self.running:
            self.running = True
            self.loop = asyncio.new_event_loop()
            self.queue = asyncio.Queue(loop=self.loop)
            self.thread = threading.Thread(target=self.run_loop, daemon=True)
            self.thread.start()

    def stop(self) -> None:
        if self.running:
            self.running = False
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self.queue.put(None), self.loop
                )

    def run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)

        async def run_tasks() -> None:
            async with Recorder(
                self.queue, self.audio, self.input_device
            ) as recorder:
                async with Player(
                    self.queue,
                    self.audio,
                    self.output_device,
                    self.delay_seconds,
                ) as player:
                    await asyncio.gather(recorder.run(), player.run())

        try:
            self.loop.run_until_complete(run_tasks())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"ERROR (AudioManager): {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                tasks = asyncio.all_tasks(loop=self.loop)
                for task in tasks:
                    task.cancel()
                self.loop.run_until_complete(
                    asyncio.gather(*tasks, return_exceptions=True)
                )
                self.loop.close()
            self.loop = None
            self.queue = None


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
            "Press next for new tongue twister, "
            "then press start and try to say the tongue twister."
        )
        self.create_widgets()

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
            font=("Segoe UI", 24),
            background=self.bg_colour,
            foreground=self.text_colour,
            anchor="center",
            padding=20,
        )

        self.style.configure("ButtonFrame.TFrame", background=self.bg_colour)

        self.style.configure(
            "TButton",
            font=("Segoe UI", 18),
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
            wraplength=self.winfo_screenwidth() - 100,
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

    def set_help(self) -> None:
        self.text_box.config(text=self.help_message)

    def get_new_tongue_twister(self) -> None:
        self.text_box.config(
            text=self.tongue_twister_manager.get_next_tongue_twister()
        )

    def start_stop_clicked(self) -> None:
        if self.audio_manager.running:
            self.audio_manager.stop()
        else:
            self.audio_manager.start()

    def quit_app(self) -> None:
        self.audio_manager.stop()
        self.destroy()


class Recorder:
    def __init__(
        self, queue: asyncio.Queue, audio: pyaudio.PyAudio, input_device: int
    ) -> None:
        self.queue = queue
        self.audio = audio
        self.input_device = input_device
        self.running = True

    async def __aenter__(self) -> Recorder:
        self.input_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.input_device,
            frames_per_buffer=CHUNK,
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.input_stream and not self.input_stream.is_stopped():
            self.running = False
            self.input_stream.stop_stream()
            self.input_stream.close()

    async def run(self) -> None:
        print("recording started")
        while self.running:
            now = time.monotonic()
            recorded_data = self.input_stream.read(CHUNK)
            await self.queue.put((now, recorded_data))
            await asyncio.sleep(EPSILON)


class Player:
    def __init__(
        self,
        queue: asyncio.Queue,
        audio: pyaudio.PyAudio,
        output_device: int,
        delay_seconds: float,
    ) -> None:
        self.queue = queue
        self.audio = audio
        self.output_device = output_device
        self.delay_seconds = delay_seconds
        self.running = True

    async def __aenter__(self) -> Player:
        self.output_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            output_device_index=self.output_device,
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.output_stream and not self.output_stream.is_stopped():
            self.running = False
            self.output_stream.stop_stream()
            self.output_stream.close()

    async def run(self) -> None:
        while True:
            item = await self.queue.get()
            if item is None:
                self.queue.task_done()
                break
            timestamp, recorded_data = item
            now = time.monotonic()
            consume_at = timestamp + self.delay_seconds
            sleep_time = max(0, consume_at - now)
            await asyncio.sleep(sleep_time)
            self.output_stream.write(recorded_data)
            self.queue.task_done()


def main(args: Namespace) -> None:
    if args.detect:
        print_available_audio_devices()
        return
    tongue_twister_manager = TongueTwistersManager("tongue_twisters.txt")
    audio_manager = AudioManager(
        args.input_device, args.output_device, args.delay_seconds
    )
    app = App(audio_manager, tongue_twister_manager)
    app.mainloop()
