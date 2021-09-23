import logging
from typing import Optional
import argparse


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")


    sub_parsers = parser.add_subparsers(help="sub-command help")

    parser_ls = sub_parsers.add_parser("ls", help="List stuff.")
    parser_ls.add_argument("filter", type=str, nargs="*",
                           help="Filter(s) for what to list.")
    # TODO: Does filtering work by OR vs AND.
    #       E.g. does #shopping #baby filter for shopping AND baby?

    parser_forget = sub_parsers.add_parser("forget")
    parser_forget.add_argument("StuffToForget", nargs="+")

    parser_tick = sub_parser.add_parser("tick")
    parser_tick.add_argument("StuffToTick", type=str, nargs="+")

    parser.add_argument("stuff", type=str, nargs="*",
                        help="Stuff you want to add...")
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
