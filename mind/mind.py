from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import argparse
import logging
import sqlite3


ID = "id"
BODY = "body"
ADD = "StuffToAdd"
DEFAULT_PATH = Path("~/.mind.db").expanduser()
STATE = "state"
TABLE = "stuff"


class State(Enum):
    ACTIVE = 0
    TICKED = 1
    FORGOTTEN = 2


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


def display(con, filters: Optional[list[str]] = None):
    print("Currently minding...")
    with con:
        cur = con.execute(f"SELECT * FROM {TABLE} ORDER BY {ID} DESC")
        for index, row in enumerate(cur.fetchmany(size=10), 1):
            print(f" {index}. {row[0]} -> {row[1]}")
        if cur.rowcount > 10:
            print("And more...")
        cur.close()


def get_db(path: Path = DEFAULT_PATH):
    if path.exists():
        logging.debug(f"Opening DB: {path}")
        return sqlite3.connect(path)
    else:
        logging.debug("Creating new, empty DB.")
        with sqlite3.connect(path) as con:
            con.execute(f"CREATE TABLE {TABLE}"
                        f"({ID} TEXT PRIMARY KEY,"
                        f"{BODY} TEXT NOT NULL,"
                        f"{STATE} INTEGER NOT NULL)")
            return con


def update_state(con, num: int, new_state: State):
    with con:
        con.execute(
            f"UPDATE {TABLE} SET {STATE}={new_state}"
            f"ORDER BY ID DESC LIMIT 1 OFFSET {num}")


def create_row(stuff: list[str]) -> tuple[str, str]:
    id = datetime.utcnow().isoformat()
    body = ' '.join(stuff)

    logging.debug(f"Writing: {id}: {body}")
    return id, body


def run(args: argparse.Namespace) -> None:
    if ADD in args:
        with get_db() as con:
            row = create_row(args.StuffToAdd)
            con.execute(f"INSERT INTO {TABLE} VALUES (?, ?, 0)", row)
        con.close()
    else:
        with get_db() as con:
            display(con)
