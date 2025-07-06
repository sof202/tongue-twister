import importlib.resources
import asyncio
import pyaudio
import time
from argparse import Namespace

FORMAT = pyaudio.paInt16
CHUNK = 1024
RATE = 44100
CHANNELS = 1
EPSILON = 1e-8


def load_tongue_twisters():
    with importlib.resources.open_text(
        "tongue_twister.data", "tongue_twisters.txt"
    ) as file:
        tongue_twisters = []
        for line in file.readlines():
            tongue_twisters.append(line.strip())
        return tongue_twisters


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


class Recorder:
    def __init__(
        self, queue: asyncio.Queue, audio: pyaudio.PyAudio, input_device: int
    ):
        self.queue = queue
        self.audio = audio
        self.input_device = input_device

    def __enter__(self):
        self.input_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.input_device,
            frames_per_buffer=CHUNK,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.input_stream and not self.input_stream.is_stopped():
            self.input_stream.stop_stream()
            self.input_stream.close()

    async def run(self) -> None:
        print("recording started")
        while True:
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
    ):
        self.queue = queue
        self.audio = audio
        self.output_device = output_device
        self.delay_seconds = delay_seconds

    def __enter__(self):
        self.output_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            output_device_index=self.output_device,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.output_stream and not self.output_stream.is_stopped():
            self.output_stream.stop_stream()
            self.output_stream.close()

    async def run(self) -> None:
        while True:
            item = await self.queue.get()
            if item is None:
                break
            timestamp, recorded_data = item
            now = time.monotonic()
            consume_at = timestamp + self.delay_seconds
            sleep_time = max(0, consume_at - now)
            await asyncio.sleep(sleep_time)
            self.output_stream.write(recorded_data)
            self.queue.task_done()


async def run_audio_loop(
    input_device: int, output_device: int, delay_seconds: float
) -> None:
    queue = asyncio.Queue()
    audio = pyaudio.PyAudio()
    with Recorder(queue, audio, input_device) as recorder:
        with Player(queue, audio, output_device, delay_seconds) as player:
            await asyncio.gather(recorder.run(), player.run())
    audio.terminate()


def main(args: Namespace) -> None:
    if args.detect:
        print_available_audio_devices()
        return
    asyncio.run(
        run_audio_loop(
            args.input_device, args.output_device, args.delay_seconds
        )
    )
