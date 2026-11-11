import argparse
from enum import StrEnum
from getpass import getuser


class Command(StrEnum):
    HELLO = "hello"


def main() -> None:
    parser = argparse.ArgumentParser(prog="soup-demo")
    parser.add_argument("command", choices=[Command.HELLO])
    parser.parse_args()
    print(f"Hello, {getuser()}!")


if __name__ == "__main__":
    main()
