from __future__ import annotations

import importlib.resources
from random import shuffle
from tongue_twister_exceptions import (
    NoTongueTwistersLoadedException,
    TongueTwisterLoadingException,
)


class TongueTwistersManager:
    def __init__(self, file: str) -> None:
        self.file = file
        self.tongue_twisters = []
        self.current_index = 0
        self.load_tongue_twisters()
        self.shuffle_tongue_twisters()

    def load_tongue_twisters(self) -> list[str]:
        try:
            with importlib.resources.open_text("data", self.file) as file:
                for line in file.readlines():
                    self.tongue_twisters.append(line.strip())
        except OSError as e:
            raise TongueTwisterLoadingException(
                f"Failed to load tongue twisters from {self.file}. "
                f"Failed with error: {e}"
            ) from e

    def shuffle_tongue_twisters(self) -> None:
        shuffle(self.tongue_twisters)

    def get_next_tongue_twister(self) -> str:
        if len(self.tongue_twisters) == 0:
            raise NoTongueTwistersLoadedException(
                "No tongue twisters have been loaded."
                f"Check if data/{self.file} is empty"
            )
        if len(self.tongue_twisters) <= self.current_index:
            self.current_index = 0
        tongue_twister = self.tongue_twisters[self.current_index]
        self.current_index += 1
        return tongue_twister
