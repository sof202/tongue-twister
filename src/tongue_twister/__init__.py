import importlib.resources


def load_tongue_twisters():
    with importlib.resources.open_text(
        "tongue_twister.data", "tongue_twisters.txt"
    ) as tongue_twisters:
        return tongue_twisters.read()
