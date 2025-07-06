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
    def __init__(self, queue: asyncio.Queue, input_stream: pyaudio.Stream):
        self.queue = queue
        self.input_stream = input_stream

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
        output_stream: pyaudio.Stream,
        delay_seconds: float,
    ):
        self.queue = queue
        self.output_stream = output_stream
        self.delay_seconds = delay_seconds

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
    input_stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=input_device,
        frames_per_buffer=CHUNK,
    )
    recorder = Recorder(queue, input_stream)
    output_stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True,
        output_device_index=output_device,
    )
    player = Player(queue, output_stream, delay_seconds)
    await asyncio.gather(recorder.run(), player.run())
    input_stream.stop_stream()
    input_stream.close()
    output_stream.close()
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
