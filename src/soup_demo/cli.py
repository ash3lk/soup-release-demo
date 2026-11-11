import argparse
from getpass import getuser


def main() -> None:
    parser = argparse.ArgumentParser(prog="soup-demo")
    parser.add_argument("command", choices=["hello"])
    parser.parse_args()
    print(f"Hello, {getuser()}!")


if __name__ == "__main__":
    main()
