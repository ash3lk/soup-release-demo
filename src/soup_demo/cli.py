import argparse
from getpass import getuser
from importlib.resources import files


def main() -> None:
    parser = argparse.ArgumentParser(prog="soup-demo")
    parser.add_argument("command", choices=["hello", "show-config"])
    args = parser.parse_args()

    if args.command == "show-config":
        config = files("soup_demo").joinpath("data").joinpath("defaults.json")
        print(config.read_text(encoding="utf-8").strip())
        return

    print(f"Hello, {getuser()}!")


if __name__ == "__main__":
    main()
