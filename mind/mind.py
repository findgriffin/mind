from datetime import datetime
from pathlib import Path
from typing import Optional
import argparse
import logging


DEFAULT_PATH = Path("~/.mind.txt").expanduser()
ADD = "StuffToAdd"


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

    parser_tick = sub_parsers.add_parser("tick")
    parser_tick.add_argument("StuffToTick", type=str, nargs="+")

    parser_add = sub_parsers.add_parser("add")
    parser_add.add_argument(ADD, type=str, nargs="+")

    parser.add_argument("stuff", type=str, nargs="*", default=None,
                        help="Stuff you want to add...")
    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose logging.")

    return parser.parse_args(argv)


def ls(db: list[str], filters: Optional[list[str]] = None):
    print("Currently minding...")
    for index, row in enumerate(db[:10], 1):
        print(f"  {index}. {row.strip()}")
    if len(db) > 10:
        print("And more...")


def get_db(path: Path = DEFAULT_PATH) -> list[str]:
    if path.exists():
        logging.debug(f"Opening DB: {path}")
        with open(path, "r") as db:
            lines = db.readlines()
            lines.sort(reverse=True)
            return lines
    else:
        logging.debug("Creating new, empty DB.")
        return []


def write_db(db: list[str], path: Path = DEFAULT_PATH):
    logging.debug(f"Writing DB with {len(db)} entries to {path}")
    with open(path, "w") as output:
        output.writelines(db)


def create_row(stuff: list[str]) -> str:
    new = f"{datetime.utcnow().isoformat()}, {' '.join(stuff)}\n"
    logging.debug(f"Writing: {new}")
    return new


def run(args: argparse.Namespace) -> None:
    if ADD in args:
        db = get_db()
        db.insert(0, create_row(args.StuffToAdd))
        write_db(db)
    else:
        db = get_db()
        ls(db)
