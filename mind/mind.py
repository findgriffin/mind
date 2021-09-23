from datetime import datetime
from enum import Enum
from pathlib import Path
from sqlite3 import Connection
from typing import Optional
import argparse
import logging
import sqlite3


ID = "id"
BODY = "body"
ADD = "StuffToAdd"
DEFAULT_PATH = Path("~/.mind.db").expanduser()
STATE = "state"
STUFF = "stuff"
TEXT = "TEXT"
INTEGER = "INTEGER"
NOT_NULL = "NOT NULL"
PRIMARY_KEY = "PRIMARY KEY"
TABLES: dict[str, tuple[tuple[str, ...], ...]] = {
    STUFF: ((ID, TEXT, NOT_NULL, PRIMARY_KEY), (BODY, TEXT, NOT_NULL),
            (STATE, INTEGER, NOT_NULL))
}


def create_cmd(name: str, schema: tuple[tuple[str, ...], ...]) -> str:
    columns = ", ".join([" ".join(column) for column in schema])
    return f"CREATE TABLE {name}({columns})"


class State(Enum):
    ACTIVE = 0
    TICKED = 1
    FORGOTTEN = 2


def add_command(sub_parsers, name, help):
    command = sub_parsers.add_parser(name)
    command.add_argument(name, type=str, nargs="+", help=help)


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")

    sub_parsers = parser.add_subparsers(help="Do '.. {cmd} -h' to get "
                                             "help for subcommands.")

    add_command(sub_parsers, "add", "Add some stuff to mind.")
    add_command(sub_parsers, "tick", "Which piece(s) of stuff to tick off.")
    add_command(sub_parsers, "list", "Which piece(s) of stuff to list.")
    add_command(sub_parsers, "forget", "Which piece of stuff to forget.")

    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose output.")

    return parser.parse_args(argv)


def query_active(con: Connection, num: Optional[int] = None) -> list[tuple]:
    cmd = f"SELECT * FROM {STUFF} WHERE state=0 ORDER BY {ID} DESC"
    if num:
        cmd += f" LIMIT 1 OFFSET {num-1}"
    with con:
        cur = con.execute(cmd)
        return cur.fetchmany(size=11)


def display(con, filters: Optional[list[str]] = None):
    print("Currently minding...")
    fetched = query_active(con)
    for index, row in enumerate(fetched[:10], 1):
        print(f" {index}. {row[0]} -> {row[1]}")
    if len(fetched) > 10:
        print("And more...")


def get_db(path: Path = DEFAULT_PATH):
    if path.exists():
        logging.debug(f"Opening DB: {path}")
        return sqlite3.connect(path)
    else:
        logging.debug("Creating new, empty DB.")
        with sqlite3.connect(path) as con:
            for name, schema in TABLES.items():
                con.execute(create_cmd(name, schema=schema))
            return con


def update_state(con, num: int, new_state: State):
    active = query_active(con, num)
    id = active[0][0]
    update = f"UPDATE {STUFF} SET {STATE}={new_state.value} WHERE id=?"
    logging.debug(f"Executing.. {update}, id={id}")
    with con:
        con.execute(update, [id])


def create_row(stuff: list[str]) -> tuple[str, str]:
    id = datetime.utcnow().isoformat()
    body = ' '.join(stuff)

    logging.debug(f"Writing: {id}: {body}")
    return id, body


def add(con: Connection, stuff: list[str]) -> str:
    row = create_row(stuff)
    with con:
        con.execute(f"INSERT INTO {STUFF} VALUES (?, ?, 0)", row)
    return row[0]


def run(args: argparse.Namespace) -> None:
    if ADD in args:
        add(get_db(), args.StuffToAdd)
    else:
        with get_db() as con:
            display(con)
    con.close()
