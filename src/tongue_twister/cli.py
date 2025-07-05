import argparse
from main import main


def parse_args():
    parser = argparse.ArgumentParser(
        prog="tongue_twister",
        description="A tongue twister game with delayed audio feedback",
    )
    parser.add_argument(
        "--delay",
        help="The delay to use between input and output in milliseconds",
        type=int,
    )
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main(parse_args())
