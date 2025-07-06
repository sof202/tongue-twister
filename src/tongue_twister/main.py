from argparse import Namespace

from core.audio_manager import AudioManager, print_available_audio_devices
from core.gui import App
from core.tongue_twister_manager import TongueTwistersManager
from tongue_twister_exceptions import (
    TongueTwisterException,
    DeviceNotFoundException,
    InvalidDeviceChannelsException,
)


def main(args: Namespace) -> None:
    if args.detect:
        print_available_audio_devices()
        return
    try:
        tongue_twister_manager = TongueTwistersManager("tongue_twisters.txt")
        audio_manager = AudioManager(
            args.input_device, args.output_device, args.delay_seconds
        )
        app = App(audio_manager, tongue_twister_manager)
        app.mainloop()
    except (DeviceNotFoundException, InvalidDeviceChannelsException) as e:
        print(f"AUDIO DEVICES ERROR: {e}")
        print("Try running with --detect to find valid audio device indexes")
    except TongueTwisterException as e:
        print(f"TONGUE TWISTER ERROR: {e}")
    except Exception as e:
        print(f"Uncaught error: {e}")
