import argparse
from getpass import getuser
from importlib.resources import files

from colorama import Fore, Style


def main() -> None:
    parser = argparse.ArgumentParser(prog="soup-demo")
    parser.add_argument("command", choices=["hello", "show-config"])
    parser.add_argument("--color", action="store_true")
    args = parser.parse_args()

    if args.command == "show-config":
        config = files("soup_demo").joinpath("data").joinpath("defaults.json")
        print(config.read_text(encoding="utf-8").strip())
        return

    greeting = f"Hello, {getuser()}!"
    if args.color:
        greeting = f"{Fore.GREEN}{greeting}{Style.RESET_ALL}"
    print(greeting)


if __name__ == "__main__":
    main()
