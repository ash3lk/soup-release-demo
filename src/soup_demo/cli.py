import argparse
import os
import pwd


def main() -> None:
    parser = argparse.ArgumentParser(prog="soup-demo")
    parser.add_argument("command", choices=["hello"])
    parser.parse_args()

    username = os.environ.get("LOGNAME") or pwd.getpwuid(os.getuid()).pw_name
    print(f"Hello, {username}!")


if __name__ == "__main__":
    main()
