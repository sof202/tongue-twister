from argparse import Namespace

from core.audio_manager import AudioManager, print_available_audio_devices
from core.gui import App
from core.tongue_twister_manager import TongueTwistersManager


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
