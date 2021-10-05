#! /usr/bin/env python3
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from sqlite3 import Connection, Cursor
from textwrap import wrap, shorten
from typing import NamedTuple, Callable, Optional, NewType, Union
import argparse
import hashlib
import logging
import sqlite3
import sys


CLEAN = "clean"
CMD = "cmd"
DEFAULT_DB = "~/.mind.db"
NEWLINE = "\n"
SPACE = " "
STUFF = "stuff"
TAG = "tag"
TAGS = "tags"
TAG_PREFIX = "#"
UTF8 = "utf-8"
PAGE_SIZE = 9
VIEW_WIDTH = 80
H_RULE = "-" * VIEW_WIDTH


State = IntEnum("State", "ABSENT ACTIVE DONE HIDDEN")
sqlite3.register_adapter(State, lambda s: s.value)
Sequence = NewType('Sequence', int)
Params = Union[dict, tuple]
Operation = tuple[str, Params]


def insert(table: str, row):
    cols = ", ".join(row._fields)
    vals = ", ".join([":" + f for f in row._fields])
    return f"INSERT INTO {table} ({cols}) VALUES ({vals})"


# None / Null not included here as there are no optional columns (yet)
# Optional[int|str] could be mapped to removing the 'NOT NULL' constraint
TYPE_MAP: dict[type, Callable[[str], str]] = {
    State: lambda n: f"INTEGER NOT NULL CHECK ({n} BETWEEN 1 AND 4)",
    Sequence: lambda n: "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
    int: lambda n: "INTEGER NOT NULL",
    float: lambda n: "REAL NOT NULL",
    str: lambda n: "TEXT NOT NULL",
    bytes: lambda n: "BLOB NOT NULL"
}


class Record(NamedTuple):
    sn: Sequence
    hash: str
    stuff: int
    before: State

    @classmethod
    def constraints(self) -> list[str]:
        return []

    def next(self):
        return Sequence(self.sn + 1)

    def parent(self):
        return Sequence(self.sn - 1)


def record_or_default(row) -> Record:
    if row:
        return Record(*row)
    else:
        return Record(Sequence(0), "", 0, State.ABSENT)


class Tag(NamedTuple):
    id: int
    tag: str

    @classmethod
    def constraints(self) -> list[str]:
        return []


def canonical_tags(tags: list[Tag]) -> str:
    return "Tags [{}]".format(", ".join([t.tag for t in tags]))


class Stuff(NamedTuple):
    id: int     # Epoch (in microseconds), ms was too course for tests.
    body: str
    state: State = State.ACTIVE

    @classmethod
    def constraints(self) -> list[str]:
        return ["PRIMARY KEY (id)"]

    def epoch(self) -> int:
        """Returns the unix epoch of this stuff in seconds, as an integer."""
        return int(self.id * 1e-6)

    def full_id(self):
        return hex(self.id)[2:]

    def created(self):
        return datetime.fromtimestamp(self.epoch()).isoformat()[:16]

    def preview(self, width=40):
        return shorten(self.body.splitlines()[0], width=width,
                       placeholder=" ...") if self.body else "EMPTY"

    def show(self, tags: list[Tag] = []) -> list[str]:
        return [f"Stuff [{self.created()}]", H_RULE, canonical_tags(tags),
                H_RULE, self.body]

    def calc_create_hash(self, parent: Record, tags: list[Tag]):
        sha = hashlib.sha1()
        canonical = "[{}][{},{}][{}]".format(
            parent.hash, self.full_id(), self.body, canonical_tags(tags))
        logging.debug(f"Canonical: {canonical}")
        sha.update(canonical.encode(UTF8))
        return sha.hexdigest()

    def calc_update_hash(self, parent: Record, new_state: State):
        sha = hashlib.sha1()
        canonical = f"[{parent.hash}][{self.full_id()},{self.state}-" \
                    f">{new_state}"
        logging.debug(f"Canonical: {canonical}")
        sha.update(canonical.encode(UTF8))
        return sha.hexdigest()

    def __str__(self):
        return f"{self.created()} -> {self.preview()}"

    def __repr__(self):
        return f"Stuff[{self.full_id()},{self.state.name},{self.body}]"

    def hash(self):
        sha = hashlib.sha1()
        sha.update(self.__repr__())
        return sha.hexdigest()


class Mind():
    tables: dict[str, type] = {STUFF: Stuff, TAGS: Tag, "log": Record}

    def __init__(self, filename: str, strict: bool = False) -> None:
        path = Path(filename).expanduser()
        exists = path.exists()
        logging.debug(f"Opening DB {path}, exists: {path.exists()}")
        with sqlite3.connect(path) as con:
            for name, schema in self.tables.items():
                create_cmd = build_create_table_cmd(name, schema)
                if exists:
                    row = con.execute("SELECT * FROM sqlite_master WHERE "
                                      "name=?", [name]).fetchone()
                    if not row or row[4] != create_cmd:
                        msg = f"Error for table {name}. Found: {row}"
                        logging.debug(msg)
                        if strict:
                            raise RuntimeError(msg)
                else:
                    con.execute(create_cmd)
            con.execute("PRAGMA foreign_keys = ON")
            self.con = con
            if not exists:
                add_content(self, [""], state=State.HIDDEN)

    def __enter__(self):
        return self

    def __exit__(self, *exc_details):
        self.con.close()

    def query(self, sql: str, params: Params) -> Cursor:
        logging.debug(f"Executing SQL   :{sql}")
        logging.debug(f"Executing PARAMS:{params}")
        return self.con.execute(sql, params)

    def tx(self, operations: list[Operation]) -> None:
        with self.con:
            logging.debug("Entered transaction.")
            [self.query(*op) for op in operations]

    def get_record(self, sn):
        cmd = "SELECT * FROM log WHERE sn = ?"
        return record_or_default(self.query(cmd, (sn,)).fetchone())

    def head(self) -> Record:
        cmd = "SELECT * FROM log ORDER BY sn DESC LIMIT 1"
        return record_or_default(self.query(cmd, ()).fetchone())

    def verify(self) -> None:
        head = self.head()
        logging.debug(f"Verifying {head}")
        if head.stuff:
            cur = self.query("SELECT * FROM stuff WHERE id=?", (head.stuff, ))
            stuff = Stuff(*cur.fetchone())
        else:
            stuff = Stuff(0, "", state=State.ABSENT)
        logging.debug(f"Stuff for Record({head.sn}): {stuff}")
        tags = QueryTags(id=stuff.id).execute(self)
        logging.debug(f"Tags for Record({head.sn}): {tags}")
        parent = self.get_record(head.parent())
        logging.debug(f"Parent for Record({head.sn}: {parent}")
        calc_hash = stuff.calc_create_hash(parent, tags)
        if calc_hash == head.hash:
            logging.debug(f"Verified: {head}")
        else:
            raise Exception(f"Hash mismatch {head}, calculated: {calc_hash}")


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

    def execute(self, mind: Mind) -> list[Stuff]:
        cur = mind.query(self.cmd(), self._asdict())
        return [Stuff(*row) for row in cur.fetchall()]


class QueryTags(NamedTuple):
    id: Optional[int]
    limit: int = 15

    def cmd(self):
        if self.id:
            return "SELECT * FROM tags WHERE id=:id ORDER BY tag ASC"
        else:
            return SPACE.join(["SELECT MAX(id), tag FROM tags GROUP BY tag",
                               "ORDER BY id DESC LIMIT :limit"])

    def execute(self, mind: Mind) -> list[Tag]:
        cur = mind.query(self.cmd(), self._asdict())
        return [Tag(*row) for row in cur.fetchall()]


def build_create_table_cmd(table_name: str, schema) -> str:
    columns = []
    for column in schema.__annotations__.items():
        name = column[0]
        columns.append(SPACE.join((name, TYPE_MAP[column[1]](column[0]))))
    const = schema.constraints()
    c_clauses = ", " + ", ".join(const) if const else ""
    return f"CREATE TABLE {table_name}({', '.join(columns)}{c_clauses})"


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


def new_stuff(hunks: list[str], state: State,
              joiner=NEWLINE) -> tuple[Stuff, list[Tag]]:
    id = int(datetime.utcnow().timestamp() * 1e6)
    cleaned: list[str] = []
    all_tags: set[str] = set()
    for hunk in hunks:
        body, tags = extract_tags(hunk)
        all_tags = all_tags.union(tags)
        cleaned.append(body)
    tag_set = [Tag(id, name) for name in sorted(all_tags)]
    return Stuff(id, joiner.join(cleaned), state), tag_set


# Always returns lowercase
def parse_filter(arg: str):
    if arg.isalnum():
        return (TAG, arg.lower())
    elif arg.startswith(TAG_PREFIX):
        return (TAG, arg[1:].lower())
    else:
        raise ValueError(f"Unknown filter: {arg}")


def order_and_filter(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    latest = CMD not in args or args.cmd != CLEAN
    try:
        filter = args.list if latest else args.clean
        return latest, filter
    except AttributeError:
        return latest, None


def do_list(mind: Mind, args: argparse.Namespace) -> list[str]:
    latest, filter = order_and_filter(args)
    logging.debug(f"Listing latest: {latest} filter: {filter}")
    filter_desc = "ALL"
    if filter:
        parsed = parse_filter(filter)
        filter_desc = "=".join(parsed)
        fetched = QueryStuff(latest=latest, tag=parsed[1],
                             limit=args.num+1).execute(mind)
    else:
        fetched = QueryStuff(latest=latest, limit=args.num+1).execute(mind)
    noun = "latest" if latest else "oldest"
    output = [f" # Currently minding [{noun}] [{filter_desc}] "
              f"[num={args.num}]...", H_RULE]
    if fetched:
        for index, row in enumerate(fetched[:args.num], 1):
            output.append(f" {index}. {row}")
    else:
        output.append("  Hmm, couldn't find anything here.")
    if len(fetched) > args.num:
        output.append("    And more...")
    tags = ", ".join([t.tag for t in QueryTags(id=None).execute(mind)])
    wrapped = wrap(f"Latest tags: {tags}", initial_indent="  ",
                   subsequent_indent=" " * 15)
    return output + [H_RULE] + wrapped + [H_RULE]


def update_state(stuff: Stuff, mind: Mind, new_state: State) -> None:
    head = mind.head()
    hash = stuff.calc_update_hash(head, new_state)
    rcd = Record(head.next(), stuff=stuff.id, before=stuff.state, hash=hash)
    ops: list[Operation] = [("UPDATE stuff SET state=:state WHERE id=:id",
                             {"id": stuff.id, "state": new_state}),
                            (insert("log", rcd), rcd._asdict())]
    mind.tx(ops)


def do_state_change(mind: Mind, args: list[str],
                    state: State) -> list[str]:
    id = parse_item(args)
    stuff = QueryStuff(limit=1, offset=id-1).execute(mind)
    if len(stuff) == 1:
        update_state(stuff[0], mind, state)
        return [f"{state.name.capitalize()}: {stuff[0]}"]
    elif len(stuff) == 0:
        return([f"Unable to find stuff: [{id}]"])
    else:
        raise RuntimeError(f"Query for 1 row returned {len(stuff)} rows.")


def do_forget(mind: Mind, args: argparse.Namespace) -> list[str]:
    return do_state_change(mind, args.forget, State.HIDDEN)


def do_tick(mind: Mind, args: argparse.Namespace) -> list[str]:
    return do_state_change(mind, args.tick, State.DONE)


def do_show(mind: Mind, args: argparse.Namespace) -> list[str]:
    id = parse_item(args.show)
    rows = QueryStuff(limit=1, offset=id-1).execute(mind)
    any(map(lambda r: logging.debug(f"Returned row: {r.__repr__()}"), rows))
    if rows:
        return rows[0].show(QueryTags(id=rows[0].id).execute(mind))
    else:
        return [f"Stuff [{id}] not found."]


def do_history(con: Connection, args: argparse.Namespace) -> list[str]:
    return ["Not implemented yet."]


def add_content(mind: Mind, content: list[str],
                state: State = State.ACTIVE) -> list[str]:
    stuff, tags = new_stuff(content, state)
    head = mind.head()
    hash = stuff.calc_create_hash(head, tags)
    logging.debug(f"Found previous: {head.sn} {head.hash}")
    logging.debug(f"Adding: {stuff.preview()} tags:{tags}, hash:{hash}")
    ops: list[Operation] = [(insert(TAGS, t), t._asdict()) for t in tags]
    ops.insert(0, (insert(STUFF, stuff), stuff._asdict()))
    record = Record(head.next(), hash, stuff.id, State.ABSENT)
    ops.append((insert("log", record), record._asdict()))
    mind.tx(ops)
    return [f"Added {stuff} {canonical_tags(tags)}"]


def do_add(mind: Mind, args: argparse.Namespace) -> list[str]:
    if args.text:
        return add_content(mind, [args.text])
    elif args.file:
        return add_content(mind, Path(args.file).read_text().splitlines())
    elif args.interactive:
        raise NotImplementedError
    else:
        raise NotImplementedError


class Command(NamedTuple):
    do: Callable
    add: Callable
    help: str


def add_command(sub_parsers, name, help, nargs=1):
    command = sub_parsers.add_parser(name)
    command.add_argument(name, type=str, nargs=nargs, help=help)
    return command


def add_list_cmd(sub_parsers, name, help):
    sub_parser = add_command(sub_parsers, name, help, nargs='?')
    sub_parser.add_argument("-n", "--num", type=int, default=PAGE_SIZE,
                            help="How much stuff to list.")


def add_add_cmd(sub_parsers, name, help):
    add = sub_parsers.add_parser(name, help=help)
    add_group = add.add_mutually_exclusive_group()
    add_group.add_argument("--file", type=str, help="Add stuff from a file.")
    add_group.add_argument("-i", "--interactive", action="store_true",
                           help="Add stuff interactively.")
    add_group.add_argument("-t", "--text", type=str,
                           help="Add text from the command line")


COMMANDS = {
    "add":      Command(do=do_add, add=add_add_cmd, help="Add stuff to mind."),
    CLEAN:      Command(do=do_list, add=add_list_cmd,
                        help="List oldest stuff, so you can clean it up ;)."),
    "forget":   Command(do_forget, add_command, "Which stuff to forget."),
    "history":  Command(do_history, add_list_cmd, "Show history of changes."),
    "list":     Command(do_list, add_list_cmd, "List your latest stuff."),
    "show":     Command(do_show, add_command, "Show stuff."),
    "tick":     Command(do_tick, add_command, "Mark stuff as complete."),
}


def run(args: argparse.Namespace) -> list[str]:
    logging.debug(f"Running with arguments: {args}")
    with Mind(args.db) as mind:
        mind.verify()
        if args.cmd in COMMANDS:
            return COMMANDS[args.cmd].do(mind, args)
        else:
            args.num = PAGE_SIZE
            return do_list(mind, args)


def setup_logging(verbose: bool = False):
    fmt = "%(levelname)s: %(message)s" if verbose else "%(message)s"
    lvl = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=lvl, format=fmt)
    logging.debug("Verbose logging enabled.")


def setup(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hello! I'm here to mind your stuff for you.")
    sub_parsers = parser.add_subparsers(
        dest=CMD, help="Do '.. {cmd} -h' to; get help for subcommands.")
    for name, cmd in COMMANDS.items():
        cmd.add(sub_parsers, name, cmd.help)
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
