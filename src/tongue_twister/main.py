import importlib.resources
import asyncio
import pyaudio
import time

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


async def recorder(queue, input_stream) -> None:
    print("recording started")
    for _ in range(550):
        now = time.monotonic()
        recorded_data = input_stream.read(CHUNK)
        await queue.put((now, recorded_data))
        await asyncio.sleep(EPSILON)

    # sentinel value for end of queue
    await queue.put(None)


async def player(queue, output_stream, delay) -> None:
    while True:
        item = await queue.get()
        if item is None:
            break
        timestamp, recorded_data = item
        now = time.monotonic()
        consume_at = timestamp + delay
        sleep_time = max(0, consume_at - now)
        await asyncio.sleep(sleep_time)
        output_stream.write(recorded_data)
        queue.task_done()
    print("finished playing")


async def run_audio_loop(delay) -> None:
    queue = asyncio.Queue()
    audio = pyaudio.PyAudio()
    input_stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=1,
        frames_per_buffer=CHUNK,
    )
    output_stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True,
    )
    await asyncio.gather(
        recorder(queue, input_stream), player(queue, output_stream, delay)
    )
    input_stream.stop_stream()
    input_stream.close()
    output_stream.close()
    audio.terminate()


def main(args):
    asyncio.run(run_audio_loop(args.delay))
