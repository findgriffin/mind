#! /usr/bin/env python3
from typing import Callable, NamedTuple
import argparse
import logging
import mind
import sys


class Command(NamedTuple):
    do: Callable
    add: Callable
    help: str


def add_command(sub_parsers, name, help):
    command = sub_parsers.add_parser(name)
    command.add_argument(name, type=str, help=help)
    return command


def add_list_cmd(sub_parsers, name, help):
    sub_parser = sub_parsers.add_parser(name)
    sub_parser.add_argument(name, type=str, help=help, nargs='?')
    sub_parser.add_argument("-n", "--num", type=int, default=mind.PAGE_SIZE,
                            help="How much stuff to list.")
    sub_parser.add_argument("-p", "--page", type=int, default=1,
                            help="Which page of results to list.")


def add_add_cmd(sub_parsers, name, help):
    add = sub_parsers.add_parser(name, help=help)
    add_group = add.add_mutually_exclusive_group()
    add_group.add_argument("--file", type=str, help="Add stuff from a file.")
    add_group.add_argument("-t", "--text", type=str,
                           help="Add text from the command line")


COMMANDS = {
    "add":      Command(do=mind.do_add, add=add_add_cmd,
                        help="Add stuff to mind."),
    mind.CLEAN: Command(do=mind.do_list, add=add_list_cmd,
                        help="List oldest stuff, so you can clean it up ;)."),
    "forget":   Command(mind.do_forget, add_command, "Which stuff to forget."),
    "history":  Command(mind.do_history, add_list_cmd,
                        help="Show history of changes."),
    "list":     Command(mind.do_list, add_list_cmd, "List your latest stuff."),
    "show":     Command(mind.do_show, add_command, "Show stuff."),
    "tick":     Command(mind.do_tick, add_command, "Mark stuff as complete."),
}


def run(args: argparse.Namespace) -> list[str]:
    logging.debug(f"Running with arguments: {args}")
    with mind.Mind(args.db) as mnd:
        if args.cmd in COMMANDS:
            return COMMANDS[args.cmd].do(mnd, args)
        else:
            args.num = mind.PAGE_SIZE
            args.page = 1
            return mind.do_list(mnd, args)


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")
    sub_parsers = parser.add_subparsers(
        dest=mind.CMD, help="Do '.. {cmd} -h' to; get help for subcommands.")
    for name, cmd in COMMANDS.items():
        cmd.add(sub_parsers, name, cmd.help)
    parser.add_argument("--db", type=str, default=mind.DEFAULT_DB,
                        help=f"DB file, defaults to {mind.DEFAULT_DB}")
    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose output.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> list[str]:
    args = setup(argv)
    mind.setup_logging(verbose=args.verbose)
    return run(args)


if __name__ == "__main__":
    for line in main(sys.argv[1:]):
        print(line)
