#! /usr/bin/env python3
from datetime import datetime
from enum import Enum
from pathlib import Path
from sqlite3 import Connection, Cursor
from textwrap import wrap, shorten
from typing import NamedTuple, Callable, Optional
import argparse
import logging
import sqlite3
import sys


ID = "id"
BODY = "body"
CMD = "cmd"
DEFAULT_DB = "~/.mind.db"
NEWLINE = "\n"
SPACE = " "
STATE = "state"
STUFF = "stuff"
TAG = "tag"
TAGS = "tags"
TAG_PREFIX = "#"
PAGE_SIZE = 9


class Cmd(Enum):
    ADD = "add"
    CLEAN = "clean"
    FORGET = "forget"
    LIST = "list"
    SHOW = "show"
    TICK = "tick"


class State(Enum):
    ACTIVE = 0
    TICKED = 1
    FORGOTTEN = 2

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.name}({self.value})"


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
    id: datetime
    tag: str


def sqlite_execute(con: Connection, sql: str, params: dict) -> Cursor:
    logging.debug(f"Executing SQL   :{sql}")
    logging.debug(f"Executing PARAMS:{params}")
    with con:
        return con.execute(sql, params)


class Stuff(NamedTuple):
    id: str
    body: str
    state: State = State.ACTIVE

    def human_id(self):
        return self.id[:16]

    def preview(self, width=40):
        return shorten(self.body.splitlines()[0], width=width,
                       placeholder=" ...") if self.body else "EMPTY"

    def show(self, tags=[]) -> list[str]:
        h_rule = "-" * 32
        tag_names = [tag.tag for tag in tags]
        tag_names.sort()
        return [f"Stuff [{self.human_id()}]", h_rule,
                "Tags: " + ", ".join(tag_names), h_rule, self.body]

    def __str__(self):
        return f"{self.human_id()} -> {self.preview()}"

    def __repr__(self):
        return f"Stuff[{self.id} -> {self.preview(width=20)}]"

    def update_state(self, con, new_state) -> None:
        sql = "UPDATE stuff SET state=:state WHERE id=:id"
        sqlite_execute(con, sql, {"id": self.id, "state": new_state})


TABLES: dict[str, type] = {"stuff": Stuff, "tags": Tag}


def add_command(sub_parsers, name, help, nargs=1):
    command = sub_parsers.add_parser(name)
    command.add_argument(name, type=str, nargs=nargs, help=help)
    return command


def parse_item(args: list[str]) -> int:
    if len(args) != 1:
        raise NotImplementedError("Only one item currently supported.")
    elif args[0].isdigit():
        return int(args[0])
    else:
        raise NotImplementedError("Only numbered items currently supported.")


class QueryStuff(NamedTuple):
    latest: bool = True
    limit: int = PAGE_SIZE + 1
    offset: int = 0
    state: State = State.ACTIVE
    tag: Optional[str] = None

    def order(self) -> str:
        return "DESC" if self.latest else "ASC"

    def cmd(self):
        parts = ["SELECT stuff.id, stuff.body FROM stuff"]
        if self.tag:
            parts.append("INNER JOIN tags ON stuff.id = tags.id ")
            parts.append("WHERE tags.tag = :tag")
            if self.state:
                parts.append("AND stuff.state = :state")
        else:
            if self.state:
                parts.append("WHERE stuff.state = :state")
        parts.append(f"ORDER BY stuff.id {self.order()}")
        parts.append("LIMIT :limit OFFSET :offset")
        return SPACE.join(parts)

    def execute(self, con: Connection) -> list[Stuff]:
        cur = sqlite_execute(con, self.cmd(), self._asdict())
        return [Stuff(*row) for row in cur.fetchall()]


class QueryTags(NamedTuple):
    id: Optional[str]
    limit: int = 15

    def cmd(self):
        if self.id:
            return "SELECT id, tag FROM tags WHERE id=:id ORDER BY tag ASC"
        else:
            return SPACE.join(["SELECT MAX(id), tag FROM tags GROUP BY tag",
                               "ORDER BY id DESC LIMIT :limit"])

    def execute(self, con: Connection) -> list[Tag]:
        cur = sqlite_execute(con, self.cmd(), self._asdict())
        return [Tag(*row) for row in cur.fetchall()]


def build_create_table_cmd(table_name: str, schema) -> str:
    columns = []
    for annotation in schema.__annotations__.items():
        name = annotation[0]
        sqlite_type = TYPE_MAP[annotation[1]].wire_type.value
        columns.append(f"{name} {sqlite_type} NOT NULL")
    return f"CREATE TABLE {table_name}({', '.join(columns)})"


def get_db(filename: str = DEFAULT_DB, strict: bool = False):
    path = Path(filename).expanduser()
    exists = path.exists()
    logging.debug(f"Opening DB {path}, exists: {path.exists()}")
    with sqlite3.connect(path) as con:
        for name, schema in TABLES.items():
            create_cmd = build_create_table_cmd(name, schema)
            if exists:
                cur = con.execute("SELECT * FROM sqlite_master WHERE "
                                  "name=?", [name])
                existing_db = cur.fetchone()[4]
                if existing_db != create_cmd:
                    msg = "Database tables do not match. Expected " \
                          f"{create_cmd}, but found {existing_db}"
                    if strict:
                        raise RuntimeError(msg)
                    else:
                        logging.debug(msg)
            else:
                con.execute(create_cmd)
        return con


def is_tag(word: str) -> Optional[str]:
    if len(word) > 1 and word.startswith(TAG_PREFIX):
        candidate = word[1:]
        if candidate.isalnum():
            return candidate.lower()
    return None


def extract_tags(raw_line: str):
    tags: set[str] = set()
    content: list[str] = []
    for word in raw_line.split():
        tag = is_tag(word)
        tags.add(tag) if tag else content.append(word)
    return SPACE.join(content), tags


def new_stuff(hunks: list[str], joiner=NEWLINE) -> tuple[Stuff, set[str]]:
    id = datetime.utcnow().isoformat()
    cleaned: list[str] = []
    all_tags: set[str] = set()
    for hunk in hunks:
        body, tags = extract_tags(hunk)
        all_tags = all_tags.union(tags)
        cleaned.append(body)
    return Stuff(id, joiner.join(cleaned), State.ACTIVE), all_tags


# Always returns lowercase
def parse_filter(arg: str):
    if arg.isalnum():
        return (TAG, arg.lower())
    elif arg.startswith(TAG_PREFIX):
        return (TAG, arg[1:].lower())
    else:
        raise ValueError(f"Unknown filter: {arg}")


def order_and_filter(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    latest = CMD not in args or args.cmd != Cmd.CLEAN.value
    try:
        filter = args.list if latest else args.clean
        return latest, filter
    except AttributeError:
        return latest, None


def do_list(con: Connection, args: argparse.Namespace) -> list[str]:
    latest, filter = order_and_filter(args)
    logging.debug(f"Listing latest: {latest} filter: {filter}")
    filter_desc = "ALL"
    if filter:
        parsed = parse_filter(filter)
        filter_desc = "=".join(parsed)
        fetched = QueryStuff(latest=latest, tag=parsed[1]).execute(con)
    else:
        fetched = QueryStuff(latest=latest).execute(con)
    noun = "latest" if latest else "oldest"
    output = [f"Currently minding {noun} [{filter_desc}]..."]
    for index, row in enumerate(fetched[:PAGE_SIZE], 1):
        output.append(f" {index}. {row}")
    if len(fetched) > PAGE_SIZE:
        output.append("And more...")
    tags = ", ".join([t.tag for t in QueryTags(id=None).execute(con)])
    return output + wrap(f"Latest tags: {tags}")


def do_state_change(con: Connection, args: list[str],
                    state: State) -> list[str]:
    id = parse_item(args)
    stuff = QueryStuff(limit=1, offset=id-1).execute(con)
    if len(stuff) == 1:
        stuff[0].update_state(con, state)
        return [f"{state.name.capitalize()}: {stuff[0]}"]
    elif len(stuff) == 0:
        return([f"Unable to find stuff: [{id}]"])
    else:
        raise RuntimeError(f"Query for 1 row returned {len(stuff)} rows.")


def do_forget(con: Connection, args: argparse.Namespace) -> list[str]:
    return do_state_change(con, args.forget, State.FORGOTTEN)


def do_tick(con: Connection, args: argparse.Namespace) -> list[str]:
    return do_state_change(con, args.tick, State.TICKED)


def do_show(con: Connection, args: argparse.Namespace) -> list[str]:
    id = parse_item(args.show)
    rows = QueryStuff(limit=1, offset=id-1).execute(con)
    tags = QueryTags(id=rows[0].id).execute(con)
    return rows[0].show(tags)


def add_content(con: Connection, content: list[str]) -> list[str]:
    logging.debug(f"Doing add: {content}")
    stuff, tags = new_stuff(content)
    with con:
        con.execute(f"INSERT INTO {STUFF} VALUES (?, ?, ?)", stuff)
        for tag in tags:
            con.execute(f"INSERT INTO {TAGS} VALUES (?, ?)", (stuff.id, tag))
    return [f"Added {stuff}"]


def do_add(con: Connection, args: argparse.Namespace) -> list[str]:
    if args.text:
        return add_content(con, [args.text])
    elif args.file:
        return add_content(con, Path(args.file).read_text().splitlines())
    elif args.interactive:
        raise NotImplementedError
    else:
        raise NotImplementedError


COMMANDS = {
    "add": do_add,
    "list": do_list,
    "forget": do_forget,
    "show": do_show,
    "tick": do_tick,
    "clean": do_list
}


def run(args: argparse.Namespace) -> list[str]:
    logging.debug(f"Running with arguments: {args}")
    with get_db(args.db) as con:
        if args.cmd in COMMANDS:
            return COMMANDS[args.cmd](con, args)
        else:
            return do_list(con, args)
    con.close()


def setup_logging(verbose: bool = False):
    fmt = "%(levelname)s: %(message)s" if verbose else "%(message)s"
    lvl = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=lvl, format=fmt)
    logging.debug("Verbose logging enabled.")


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")

    sub_parsers = parser.add_subparsers(dest=CMD,
                                        help="Do '.. {cmd} -h' to; get help "
                                             "for subcommands.")

    add = sub_parsers.add_parser(Cmd.ADD.value,
                                 help="Add stuff to mind.")
    add_group = add.add_mutually_exclusive_group()
    add_group.add_argument("--file", type=str, help="Add stuff from a file.")
    add_group.add_argument("-i", "--interactive", action="store_true",
                           help="Add stuff interactively")
    add_group.add_argument("-t", "--text", type=str,
                           help="Add text from the command line")

    add_command(sub_parsers, Cmd.SHOW.value, "Show stuff.")
    add_command(sub_parsers, Cmd.TICK.value, "Which stuff to tick off.")
    add_command(sub_parsers, Cmd.LIST.value, nargs="?",
                help="List your latest stuff.")
    add_command(sub_parsers, Cmd.FORGET.value, "Which stuff to forget.")
    add_command(sub_parsers, Cmd.CLEAN.value, nargs='?',
                help="List your oldest stuff, so you can clean it up ;).")
    parser.add_argument("--db", type=str, default=DEFAULT_DB,
                        help=f"DB file, defaults to {DEFAULT_DB}")
    parser.add_argument("-v", "--verbose",  action="store_true",
                        help="Enable verbose output.")

    return parser.parse_args(argv)


if __name__ == "__main__":
    args = setup(sys.argv[1:])
    setup_logging(verbose=args.verbose)
    for line in run(args):
        print(line)
