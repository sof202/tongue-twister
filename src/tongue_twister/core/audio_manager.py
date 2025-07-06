from __future__ import annotations

import asyncio
import threading
import time
from types import TracebackType
from typing import Optional, Type
from tongue_twister_exceptions import (
    DeviceNotFoundException,
    InvalidDeviceChannelsException,
)

import pyaudio

FORMAT = pyaudio.paInt24
CHUNK = 2048
RATE = 48000
CHANNELS = 1
EPSILON = 1e-8


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
        self.check_audio_devices()

    def check_audio_devices(self) -> None:
        info = self.audio.get_host_api_info_by_index(0)
        number_of_devices = info.get("deviceCount")
        if self.input_device > number_of_devices:
            raise DeviceNotFoundException(
                f"Input device doesn't exist - {self.input_device}"
            )
        if self.output_device > number_of_devices:
            raise DeviceNotFoundException(
                f"Output device doesn't exist - {self.output_device}"
            )
        if (
            self.audio.get_device_info_by_host_api_device_index(
                0, self.input_device
            ).get("maxInputChannels")
            < 1
        ):
            raise InvalidDeviceChannelsException(
                "Input device has no input channels"
            )
        if (
            self.audio.get_device_info_by_host_api_device_index(
                0, self.output_device
            ).get("maxOutputChannels")
            < 1
        ):
            raise InvalidDeviceChannelsException(
                "Output device has no output channels"
            )

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
