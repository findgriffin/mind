#! /usr/bin/env python3
from datetime import datetime as dt, timezone as tz
from enum import IntEnum, Enum
from pathlib import Path
from sqlite3 import Cursor, PARSE_DECLTYPES
from textwrap import wrap, shorten
from typing import NamedTuple, Callable, Optional, NewType, Union
import argparse
import hashlib
import logging
import sqlite3


CLEAN = "clean"
CMD = "cmd"
DEFAULT_DB = "~/.mind.db"
MICROS = 1e6
NEWLINE = "\n"
SPACE = " "
STUFF = "stuff"
TAGS = "tags"
PAGE_SIZE = 9
H_RULE = "-" * 80


Phase = IntEnum("Phase", "ABSENT ACTIVE DONE HIDDEN")
FilterType = Enum("FilterType", (("ALL", None), ("TAG", "#")))
sqlite3.register_adapter(Phase, lambda s: s.value)
sqlite3.register_converter("PHASE", lambda b: Phase(int(b)))
Sequence = NewType('Sequence', int)
Params = Union[dict, tuple]
Operation = tuple[str, Params]


class Order(Enum):
    LATEST = "DESC"
    OLDEST = "ASC"


def to_order(latest: bool) -> Order:
    return Order.LATEST if latest else Order.OLDEST


class IntegrityError(Exception):
    pass


class Transition(Enum):
    ADD = (Phase.ABSENT, Phase.ACTIVE)
    FORGET = (Phase.ACTIVE, Phase.HIDDEN)
    TICK = (Phase.ACTIVE, Phase.DONE)
    UNFORGET = (Phase.HIDDEN, Phase.ACTIVE)
    UNTICK = (Phase.DONE, Phase.ACTIVE)
    INIT = (Phase.ABSENT, Phase.HIDDEN)

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return f"Phases [{self.value[0].name}->{self.value[1].name}]"


class Epoch(int):

    def __str__(self):
        return dt.fromtimestamp(self / MICROS, tz.utc).isoformat()[:16]

    def __repr__(self):
        return hex(self)[2:]

    @classmethod
    def now(cls):
        return cls(dt.now(tz=tz.utc).timestamp() * MICROS)


sqlite3.register_adapter(Epoch, lambda e: e)
sqlite3.register_converter("EPOCH", lambda b: Epoch(int(b)))


def insert(table: str, row):
    cols = ", ".join(row._fields)
    vals = ", ".join([":" + f for f in row._fields])
    return f"INSERT INTO {table} ({cols}) VALUES ({vals})"


# None / Null not included here as there are no optional columns (yet)
# Optional[int|str] could be mapped to removing the 'NOT NULL' constraint
TYPE_MAP: dict[type, Callable[[str], str]] = {
    Phase: lambda n: f"PHASE NOT NULL CHECK ({n} BETWEEN 1 AND 4)",
    Sequence: lambda n: "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
    Epoch: lambda n: "EPOCH NOT NULL",
    int: lambda n: "INTEGER NOT NULL",
    float: lambda n: "REAL NOT NULL",
    str: lambda n: "TEXT NOT NULL",
    bytes: lambda n: "BLOB NOT NULL"
}


class Record(NamedTuple):
    sn: Sequence = Sequence(0)
    hash: str = ""
    stuff: Epoch = Epoch(0)
    stamp: Epoch = Epoch(0)
    old_state: Phase = Phase.ABSENT
    new_state: Phase = Phase.HIDDEN

    def __str__(self):
        return f"Record [{self.sn}, {self.stamp}, {self.hash}, " \
               f"{self.stuff!r}, {self.old_state.name}->{self.new_state.name}]"

    def __bool__(self):
        return self.sn > 0

    @classmethod
    def constraints(self) -> list[str]:
        return []

    def next(self):
        return Sequence(self.sn + 1)

    def parent(self):
        return Sequence(self.sn - 1)

    def canonical(self):
        return f"Record [{self.sn},{self.hash}]"

    def act(self) -> Transition:
        return Transition((self.old_state, self.new_state))


class Tag(NamedTuple):
    id: Epoch
    tag: str

    @classmethod
    def constraints(self) -> list[str]:
        return []


class Tags(list[Tag]):

    @classmethod
    def from_grouped(cls, id: Epoch, grouped: Optional[str]):
        parts = grouped.split(",") if grouped else []
        return Tags([Tag(id, t) for t in parts])

    def canonical(self) -> str:
        return "Tags [{}]".format(", ".join([t.tag for t in sorted(self)]))


class Stuff(NamedTuple):
    id: Epoch     # Epoch (in microseconds), ms was too course for tests.
    body: str
    state: Phase = Phase.ACTIVE

    @classmethod
    def constraints(self) -> list[str]:
        return ["PRIMARY KEY (id)"]

    def preview(self, width=40):
        return shorten(self.body.splitlines()[0], width=width,
                       placeholder=" ...") if self.body else "EMPTY"

    def show(self, tags: Tags = Tags()) -> list[str]:
        return [f"[Created {self.id}] {tags.canonical()}",
                self.body, "-" * 40]

    def canonical(self, phase: Optional[Phase] = None):
        if not phase:
            phase = self.state
        body = self.body if phase == Phase.ACTIVE else ""
        return f"Stuff [{self.id!r},{body}]"

    def __str__(self):
        return f"{self.id} -> {self.preview()}"

    def __repr__(self):
        return f"Stuff[{self.id!r},{self.state.name},{self.body}]"

    def hash(self):
        return hashlib.sha1(self.__repr__()).hexdigest()


class Change(NamedTuple):
    parent: Record
    stuff: Stuff
    act: Transition
    stamp: Epoch
    tags: Tags = Tags()

    def canonical(self) -> str:
        parts = [self.parent.canonical(), self.stuff.canonical(
            self.act.value[1]), repr(self.act), self.tags.canonical()]
        return "Change [{}]".format(",".join(parts))

    def hash(self) -> str:
        return hashlib.sha1(self.canonical().encode("utf-8")).hexdigest()

    def record(self) -> Record:
        return Record(self.parent.next(), self.hash(), self.stuff.id,
                      self.stamp, self.act.value[0], self.act.value[1])


class Mind():
    tables: dict[str, type] = {STUFF: Stuff, TAGS: Tag, "log": Record}

    def __init__(self, filename: str, strict: bool = False) -> None:
        self.strict = strict
        path = Path(filename).expanduser()
        exists = path.exists() and path.stat().st_size
        logging.debug(f"Opening DB {path}, exists: {path.exists()}")
        with sqlite3.connect(path, detect_types=PARSE_DECLTYPES) as con:
            con.execute("PRAGMA foreign_keys = ON")
            self.con = con
            if not exists:
                for name, schema in self.tables.items():
                    con.execute(build_create_table_cmd(name, schema))
                add_content(self, [""], state=Phase.HIDDEN, parent=Record())
        self.verify() if self.strict else self.verify(10)

    def __enter__(self):
        return self

    def __exit__(self, *exc_details):
        self.verify() if self.strict else self.verify(3)
        self.con.close()

    def query(self, sql: str, params: Params) -> Cursor:
        logging.debug(f"Executing SQL   :{sql}")
        logging.debug(f"Executing PARAMS:{params}")
        return self.con.execute(sql, params)

    def tx(self, operations: list[Operation]) -> None:
        with self.con:
            logging.debug("Entered transaction.")
            [self.query(*op) for op in operations]

    def get_full_record(self, sn) -> tuple[Record, Stuff, Tags]:
        row = self.query("SELECT log.*, stuff.*, group_concat(tags.tag) "
                         "FROM log INNER JOIN stuff ON log.stuff = stuff.id "
                         "LEFT JOIN tags ON stuff.id = tags.id "
                         "WHERE log.sn = :sn",
                         {"sn": sn}).fetchone()
        stuff = Stuff(*row[6:9])
        return (Record(*row[:6]), stuff, Tags.from_grouped(stuff.id, row[9]))

    def head(self) -> Record:
        cmd = "SELECT * FROM log ORDER BY sn DESC LIMIT 1"
        return Record(*self.query(cmd, ()).fetchone())

    def _verify(self, record: Record, stuff: Stuff,
                tags: Tags) -> tuple[Record, Stuff, Tags]:
        logging.debug(f"Verifying {record}, {stuff}")
        is_active = record.new_state == Phase.ACTIVE
        tags = tags if is_active else Tags()
        parent, p_stuff, p_tags = self.get_full_record(record.parent())
        change = Change(parent, stuff, record.act(), record.stamp, tags)
        calc_hash = change.hash()
        computed = f"Computed: {calc_hash} <- {change.canonical()}"
        logging.debug(computed)
        if calc_hash == record.hash:
            logging.debug(f"Verified: {record}")
        else:
            raise IntegrityError(f"Hash mismatch\nRetrieved: {record}\n"
                                 f"Computed: {computed}")
        return parent, p_stuff, p_tags

    def verify(self, depth: Optional[int] = None) -> None:
        try:
            head = self.head()
            stop = max(head.sn - depth if depth else 1, 1)
            record, stuff, tags = self.get_full_record(head.sn)
            for i in range(head.sn, stop, -1):
                record, stuff, tags = self._verify(record, stuff, tags)
        except IntegrityError as err:
            raise err
        except Exception as exc:
            raise IntegrityError(f"Unknown error {exc}")


def parse_item(args: str) -> list[int]:
    return [int(arg) for arg in args.split(',')]


class QueryStuff(NamedTuple):
    order: Order = Order.LATEST
    limit: int = PAGE_SIZE + 1
    offset: int = 0
    state: Phase = Phase.ACTIVE
    tag: Optional[str] = None

    def cmd(self):
        join1 = "INNER JOIN tags ON stuff.id = tags.id" if self.tag else ""
        join2 = "AND tags.tag = :tag" if self.tag else ""
        return f"SELECT stuff.id, stuff.body FROM stuff {join1} "\
               f"WHERE stuff.state = :state {join2} " \
               f"ORDER BY stuff.id {self.order.value} LIMIT :limit OFFSET " \
               f":offset"

    def fetchall(self, mind: Mind) -> list[Stuff]:
        cur = mind.query(self.cmd(), self._asdict())
        return [Stuff(*row) for row in cur.fetchall()]

    def fetchone(self, mind: Mind) -> Optional[Stuff]:
        row = mind.query(self.cmd(), self._asdict()).fetchone()
        return Stuff(*row) if row else None


class QueryTags(NamedTuple):
    id: Optional[int]
    limit: int = 15

    def cmd(self):
        if self.id:
            return "SELECT * FROM tags WHERE id=:id ORDER BY tag ASC"
        else:
            return "SELECT MAX(id), tag FROM tags GROUP BY tag " \
                   "ORDER BY id DESC LIMIT :limit"

    def execute(self, mind: Mind) -> Tags:
        cur = mind.query(self.cmd(), self._asdict())
        return Tags([Tag(*row) for row in cur.fetchall()])


def build_create_table_cmd(table_name: str, schema) -> str:
    cols = schema.__annotations__.items()
    columns = [SPACE.join((col[0], TYPE_MAP[col[1]](col[0]))) for col in cols]
    const = schema.constraints()
    c_clauses = ", " + ", ".join(const) if const else ""
    return f"CREATE TABLE {table_name}({', '.join(columns)}{c_clauses})"


def is_tag(word: str) -> Optional[str]:
    if len(word) > 1 and word.startswith(FilterType.TAG.value):
        candidate = word[1:]
        if candidate.isalnum():
            return candidate.lower()
    return None


def extract_tags(raw_line: str) -> tuple[str, set[str]]:
    tags: set[str] = set()
    content: list[str] = []
    for word in raw_line.split():
        tag = is_tag(word)
        tags.add(tag) if tag else content.append(word)
    return SPACE.join(content), tags


def new_stuff(hunks: list[str], state: Phase,
              joiner=NEWLINE) -> tuple[Stuff, Tags, Epoch]:
    now = Epoch.now()
    cleaned: list[str] = []
    all_tags: set[str] = set()
    for hunk in hunks:
        body, tags = extract_tags(hunk)
        all_tags = all_tags.union(tags)
        cleaned.append(body)
    tag_set = Tags([Tag(now, name) for name in sorted(all_tags)])
    return Stuff(now, joiner.join(cleaned), state), tag_set, now


class Filter(NamedTuple):
    ft: FilterType = FilterType.ALL
    val: Optional[str] = None

    def __str__(self):
        return f"{self.ft.name}={self.val}" if self.val else self.ft.name


def parse_filter(arg: Optional[str]) -> Filter:
    if arg:
        if arg.isalnum():
            return Filter(ft=FilterType.TAG, val=arg.lower())
        else:
            for ft in FilterType:
                if ft.value and arg.startswith(ft.value):
                    return Filter(ft, arg.lstrip(ft.value))
            raise ValueError(f"Unknown filter: {arg}")
    else:
        return Filter()


def order_and_filter(args: argparse.Namespace) -> tuple[Order, Optional[str]]:
    latest = CMD not in args or args.cmd != CLEAN
    order = to_order(latest)
    try:
        filter = args.list if latest else args.clean
        return order, filter
    except AttributeError:
        return order, None


def do_list(mind: Mind, args: argparse.Namespace) -> list[str]:
    order, filter_arg = order_and_filter(args)
    filter = parse_filter(filter_arg)
    logging.debug(f"Listing {order.name} filter: {filter}")
    offset = (args.page - 1) * args.num
    fetched = QueryStuff(order=order, tag=filter.val, offset=offset,
                         limit=args.num+1).fetchall(mind)
    output = [f" # Currently minding [{order.name.lower()}] [{filter}] "
              f"[num={args.num}]...", H_RULE]
    if fetched:
        for index, row in enumerate(fetched[:args.num], 1):
            output.append(f" {index}. {row}")
    else:
        output.append("  Hmm, couldn't find anything here.")
    if len(fetched) > args.num:
        output.append("    And more...")
    tags = ", ".join([t.tag for t in QueryTags(id=None).execute(mind)])
    shortened = shorten(f"Latest tags: {tags}", width=70,
                        placeholder=" ...")
    return output + [H_RULE, "  " + shortened, H_RULE]


def update_state(old_stuff: Stuff, mind: Mind, new_state: Phase) -> str:
    change = Change(mind.head(), old_stuff,
                    Transition((old_stuff.state, new_state)), Epoch.now())
    logging.debug(f"Canonical update: {change.canonical()}")
    rcd = change.record()
    ops: list[Operation] = [("UPDATE stuff SET state=:state WHERE id=:id",
                             {"id": old_stuff.id, "state": new_state}),
                            (insert("log", rcd), rcd._asdict())]
    mind.tx(ops)
    return f"{new_state.name.capitalize()}: {old_stuff}"


def find_by_ids(mind: Mind, id_arg: str) -> tuple[list[Stuff], list[str]]:
    found: list[Stuff] = []
    not_found: list[str] = []
    for id in parse_item(id_arg):
        stuff = QueryStuff(limit=1, offset=id-1).fetchone(mind)
        fail_msg = f"Stuff with ID {id} not found."
        found.append(stuff) if stuff else not_found.append(fail_msg)
    return found, not_found


def prepare_change(mind: Mind, id_arg: str,
                   action, check=True) -> tuple[list[Stuff], list[str]]:
    found, not_found = find_by_ids(mind, id_arg)
    if not_found:
        return [], not_found
    else:
        print(f"Confirm that you want to {action} the following items:")
        for item in found:
            print(str(item))
        answer = input("Answer 'y' or 'yes' to continue: ")
        if answer.lower() in ["y", "yes"]:
            return found, not_found
        else:
            return [], [f"Ok, will not {action} anything."]


def do_forget(mind: Mind, args: argparse.Namespace) -> list[str]:
    changes, not_found = prepare_change(mind, args.forget, "forget")
    if changes:
        return [update_state(stuff, mind, Phase.HIDDEN) for stuff in changes]
    else:
        return not_found


def do_tick(mind: Mind, args: argparse.Namespace) -> list[str]:
    changes, not_found = prepare_change(mind, args.tick, "tick")
    if changes:
        return [update_state(stuff, mind, Phase.DONE) for stuff in changes]
    else:
        return not_found


def do_show(mind: Mind, args: argparse.Namespace) -> list[str]:
    output = []
    for id in parse_item(args.show):
        rows = QueryStuff(limit=1, offset=id-1).fetchall(mind)
        any(map(lambda r: logging.debug(f"Returned: {r.__repr__()}"), rows))
        if rows:
            output.extend(rows[0].show(QueryTags(id=rows[0].id).execute(mind)))
        else:
            output.append(f"Stuff [{id}] not found.")
    return output


def hist_row(row: tuple[int, str, Epoch, Epoch, Phase, Phase, str,
                        Optional[str]]) -> str:
    stuff = Stuff(id=row[2], body=row[6], state=row[5]).preview()
    tags = "Tags [{}]".format(row[7] or " ")
    command = Transition((row[4], row[5]))
    return f"{row[0]}. {row[1][:6]} {command:>7} {row[3]} -> {stuff} {tags}"


def do_history(mind: Mind, args: argparse.Namespace) -> list[str]:
    cur = mind.query("SELECT log.*, stuff.body, group_concat(tags.tag) "
                     "FROM log INNER JOIN stuff ON log.stuff = stuff.id "
                     "LEFT JOIN tags ON stuff.id = tags.id "
                     "GROUP BY log.sn ORDER BY log.sn DESC "
                     "LIMIT :limit OFFSET :offset ",
                     {"offset": (args.page - 1) * args.num, "limit": args.num})
    return [hist_row(row) for row in cur.fetchall()]


def add_content(mind: Mind, content: list[str], state: Phase = Phase.ACTIVE,
                parent: Optional[Record] = None) -> tuple[Stuff, Tags]:
    stuff, tags, timestamp = new_stuff(content, state)
    logging.debug(f"Adding: {stuff.preview()} tags:{tags}")
    change = Change(mind.head() if parent is None else parent, stuff,
                    Transition((Phase.ABSENT, state)), timestamp, tags)
    logging.debug(f"Canonical change: {change.canonical()}")
    record = change.record()
    logging.debug(f"New record: {record}")
    ops: list[Operation] = [(insert(TAGS, t), t._asdict()) for t in tags]
    ops.insert(0, (insert(STUFF, stuff), stuff._asdict()))
    ops.append((insert("log", record), record._asdict()))
    mind.tx(ops)
    return stuff, tags


def get_content(args: argparse.Namespace) -> list[str]:
    if args.text:
        return [args.text]
    elif args.file:
        return Path(args.file).read_text().splitlines()
    else:
        return [input("Add stuff: ")]


def do_add(mind: Mind, args: argparse.Namespace) -> list[str]:
    stuff, tags = add_content(mind, get_content(args))
    return [f"Added {stuff} {tags.canonical()}"]


def setup_logging(verbose: bool = False):
    fmt = "%(levelname)s: %(message)s" if verbose else "%(message)s"
    lvl = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=lvl, format=fmt)
    logging.debug("Verbose logging enabled.")
