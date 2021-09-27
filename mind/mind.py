from datetime import datetime
from enum import Enum
from pathlib import Path
from sqlite3 import Connection
from typing import NamedTuple, Callable, Optional
import argparse
import logging
import sqlite3

ID = "id"
BODY = "body"
DEFAULT_DB = "~/.mind.db"
DOTS = "..."
SPACE = " "
STATE = "state"
STUFF = "stuff"
TAG = "tag"
TAGS = "tags"
TAG_PREFIX = "#"
TEXT = "TEXT"
INTEGER = "INTEGER"
NOT_NULL = "NOT NULL"
PAGE_SIZE = 9
PREVIEW_LENGTH = 40
PRIMARY_KEY = " PRIMARY KEY "


def create_cmd(name: str, schema: tuple[tuple[str, ...], ...]) -> str:
    columns = ", ".join([" ".join(column) for column in schema])
    return f"CREATE TABLE {name}({columns})"


class Cmd(Enum):
    ADD = "add"
    CLEAN = "clean"
    FORGET = "forget"
    LIST = "list"
    TICK = "tick"


class State(Enum):
    ACTIVE = 0
    TICKED = 1
    FORGOTTEN = 2


class SQLiteType(Enum):
    NULL = "NULL"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"


class SQLiteMapping(NamedTuple):
    wire_type: SQLiteType
    converter: Optional[Callable] = None
    adapter: Optional[Callable] = None


state_mapping = SQLiteMapping(wire_type=SQLiteType.INTEGER,
                              adapter=lambda s: s.value,
                              converter=State.__init__)
dt_mapping = SQLiteMapping(
    wire_type=SQLiteType.INTEGER,
    adapter=lambda dt: dt.timestamp(),
    converter=datetime.fromtimestamp)

# None / Null not included here as there are no optional columns (yet)
# Optional[int|str] could be mapped to removing the 'NOT NULL' constraint
TYPE_MAP: dict[type, SQLiteMapping] = {
    State: state_mapping,
    datetime: dt_mapping,
    int:    SQLiteMapping(wire_type=SQLiteType.INTEGER),
    float:  SQLiteMapping(wire_type=SQLiteType.REAL),
    str:    SQLiteMapping(wire_type=SQLiteType.TEXT),
    bytes:  SQLiteMapping(wire_type=SQLiteType.BLOB)
}

for t, mapping in TYPE_MAP.items():
    if mapping.adapter:
        sqlite3.register_adapter(t, mapping.adapter)
    if mapping.converter:
        sqlite3.register_converter(t.__name__, mapping.converter)


class Tag(NamedTuple):
    stuff_id: datetime
    tag: str


class Stuff(NamedTuple):
    id: str
    body: str
    state: State = State.ACTIVE

    def human_id(self):
        return self[0][:16]

    def preview(self, length=PREVIEW_LENGTH):
        first_line = self[1].splitlines()[0]
        if len(first_line) > length:
            return first_line[:length].strip() + DOTS
        else:
            return first_line

    def __str__(self):
        return f"{self.human_id()} -> {self.preview()}"

    def __repr__(self):
        return f"Stuff[{self[0]} -> {self.preview(length=20)}]"


TABLES: dict[str, type] = {"stuff": Stuff, "tags": Tag}


def create_cmd2(table_name: str, schema) -> str:
    columns = []
    for annotation in schema.__annotations__.items():
        name = annotation[0]
        sqlite_type = TYPE_MAP[annotation[1]].wire_type.value
        columns.append(f"{name} {sqlite_type} NOT NULL")
    return f"CREATE TABLE {table_name}({', '.join(columns)})"


def add_command(sub_parsers, name, help, nargs=1):
    command = sub_parsers.add_parser(name)
    command.add_argument(name, type=str, nargs=nargs, help=help)


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")

    sub_parsers = parser.add_subparsers(help="Do '.. {cmd} -h' to get "
                                             "help for subcommands.")

    add_command(sub_parsers, Cmd.ADD.value, "Add stuff to mind.", nargs="+")
    add_command(sub_parsers, Cmd.TICK.value, "Which stuff to tick off.")
    add_command(sub_parsers, Cmd.LIST.value, "List your latest stuff.")
    add_command(sub_parsers, Cmd.FORGET.value, "Which stuff to forget.")
    add_command(sub_parsers, Cmd.CLEAN.value,
                "List your oldest stuff, so you can clean it up ;).")
    parser.add_argument("--db", type=str, default=DEFAULT_DB,
                        help=f"DB file, defaults to {DEFAULT_DB}")
    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose output.")

    return parser.parse_args(argv)


def parse_item(args: list[str]) -> int:
    if len(args) != 1:
        raise ValueError("Expected one argument.")
    elif args[0].isdigit():
        return int(args[0])
    else:
        raise ValueError(f"Argument {args[0]} is invalid, must be an int.")


def query_stuff(con: Connection, *, state=State.ACTIVE, latest: bool = True,
                limit: int = PAGE_SIZE+1, start: int = 1) -> list[Stuff]:
    order = "DESC" if latest else "ASC"
    with con:
        cur = con.execute(f"SELECT * FROM {STUFF} WHERE state={state.value} "
                          f"ORDER BY {ID} {order} LIMIT {limit} "
                          f"OFFSET {start-1}")
        return [Stuff(*row) for row in cur.fetchall()]


def query_tags(con: Connection, tag, *, latest: bool = True) -> list[Tag]:
    order = "DESC" if latest else "ASC"
    with con:
        cur = con.execute(f"SELECT * FROM {TAGS} WHERE {TAG}=? "
                          f"ORDER BY stuff_id {order}", [tag])
        return [Tag(*row) for row in cur.fetchall()]


def get_db(filename: str = DEFAULT_DB):
    path = Path(filename).expanduser()
    if path.exists():
        logging.debug(f"Opening DB: {path}")
        return sqlite3.connect(path)
    else:
        logging.debug("Creating new, empty DB.")
        with sqlite3.connect(path) as con:
            for name, schema in TABLES.items():
                con.execute(create_cmd2(name, schema))
            return con


def update_state(con, num: int, new_state: State):
    active = query_stuff(con, limit=1, start=num)
    id = active[0][0]
    update = f"UPDATE {STUFF} SET {STATE}={new_state.value} WHERE id=?"
    logging.debug(f"Executing.. {update}, id={id}")
    with con:
        con.execute(update, [id])


def extract_tags(raw_line: str):
    tags: set[str] = set()
    content: list[str] = []
    for word in raw_line.split():
        if len(word) > 1 and word.startswith(TAG_PREFIX):
            tags.add(word[1:])
        else:
            content.append(word)
    return SPACE.join(content), tags


def new_stuff(hunks: list[str], joiner=SPACE) -> tuple[Stuff, set[str]]:
    id = datetime.utcnow().isoformat()
    cleaned: list[str] = []
    all_tags: set[str] = set()
    for hunk in hunks:
        body, tags = extract_tags(hunk)
        all_tags = all_tags.union(tags)
        cleaned.append(body)
    return Stuff(id, joiner.join(cleaned), State.ACTIVE), all_tags


def do_add(con: Connection, args: list[str]) -> list[str]:
    logging.debug(f"Doing add: {args}")
    stuff, tags = new_stuff(args)
    with con:
        con.execute(f"INSERT INTO {STUFF} VALUES (?, ?, ?)", stuff)
        for tag in tags:
            con.execute(f"INSERT INTO {TAGS} VALUES (?, ?)", (stuff.id, tag))
    return [f"Added {stuff}"]


def do_list(con: Connection, *, args: list[str] = None,
            clean=False) -> list[str]:
    output = ["Currently minding..."]
    fetched = query_stuff(con, latest=not clean)
    for index, row in enumerate(fetched[:PAGE_SIZE], 1):
        output.append(f" {index}. {row}")
    if len(fetched) > PAGE_SIZE:
        output.append("And more...")
    return output


def do_state_change(con: Connection, name: str,
                    args: list[str], state: State) -> list[str]:
    id = parse_item(args)
    stuff = query_stuff(con, limit=1, start=id)
    if len(stuff) == 1:
        update_state(con, id, state)
        return [f"{state.name.capitalize()}: {stuff[0]}"]
    elif len(stuff) == 0:
        return([f"Unable to find stuff: [{id}]"])
    else:
        raise RuntimeError(f"Query for 1 row returned {len(stuff)} rows.")


def do_forget(con: Connection, args: list[str]):
    return do_state_change(con, Cmd.FORGET.name, args, State.FORGOTTEN)


def do_tick(con: Connection, args: list[str]):
    return do_state_change(con, Cmd.TICK.name, args, State.TICKED)


def run(args: argparse.Namespace) -> list[str]:
    logging.debug(f"Running with arguments: {args}")
    with get_db(args.db) as con:
        if Cmd.ADD.value in args:
            return do_add(con, args.add)
        elif Cmd.LIST.value in args:
            return do_list(con, args=args.list)
        elif Cmd.FORGET.value in args:
            return do_forget(con, args.forget)
        elif Cmd.TICK.value in args:
            return do_tick(con, args.tick)
        elif Cmd.CLEAN.value in args:
            return do_list(con, args=args.clean, clean=True)
        else:
            return do_list(con)
    con.close()
