import wave

import pyaudio
import math


FORMAT = pyaudio.paInt16
CHUNK = 512
RATE = 44100
RECORD_SECONDS = 5
CHANNELS = 1
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "recordedFile.wav"


audio = pyaudio.PyAudio()

print("----device list------------------------------------------------")
info = audio.get_host_api_info_by_index(0)
numdevices = info.get("deviceCount")
for i in range(0, numdevices):
    if (
        audio.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
    ) > 0:
        print(
            "Input Device id ",
            i,
            " - ",
            audio.get_device_info_by_host_api_device_index(0, i).get("name"),
        )
    if (
        audio.get_device_info_by_host_api_device_index(0, i).get("maxOutputChannels")
    ) > 0:
        print(
            "Output Device id ",
            i,
            " - ",
            audio.get_device_info_by_host_api_device_index(0, i).get("name"),
        )
print("-------------------------------------------------------------")

index = int(input())
print("recording via index " + str(index))

in_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=index,
    frames_per_buffer=CHUNK,
)
out_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True,
)
print("recording started")
Recordframes = []

for i in range(0, math.ceil(RATE / CHUNK * RECORD_SECONDS)):
    out_stream.write(in_stream.read(CHUNK))

in_stream.stop_stream()
in_stream.close()
out_stream.close()
audio.terminate()
