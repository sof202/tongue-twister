class TongueTwisterException(Exception):
    """Base exception class for tongue-twister-based errors"""

    pass


class DeviceNotFoundException(TongueTwisterException):
    """Exception for when a device is not found"""

    pass


class InvalidDeviceChannelsException(TongueTwisterException):
    """Exception for when an audio device has incorrect channels"""

    pass


class NoTongueTwistersLoadedException(TongueTwisterException):
    """Exception for when no tongue twisters could be loaded"""

    pass


class TongueTwisterLoadingException(TongueTwisterException):
    """Exception for when a problem occurs during tongue twister loading"""

    pass
