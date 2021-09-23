import logging
from typing import Optional
import argparse


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="This is a Python 3 project.")
    parser.add_argument("--name", type=str, required=False,
                        help="Your name, for example 'Margaret'.")
    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose logging.")
    return parser.parse_args(argv)


def run(name: Optional[str] = None) -> str:
    if name:
        logging.debug("Name given.")
        return f"Hello, {name}!"
    else:
        logging.debug("No name given.")
        return "Hello, world!"
