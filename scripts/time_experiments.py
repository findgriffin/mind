#! /usr/bin/env python3

import sqlite3
from time import sleep


def single_table():
    with sqlite3.connect(":memory:") as con:
        con.execute("CREATE TABLE a(sn INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "ts INT NOT NULL DEFAULT (cast(strftime('%s', 'now') as int)),"
                    "hash TEXT NOT NULL)")
        con.execute("INSERT INTO a(hash) VALUES ('foo')")
        sleep(1)
        con.execute("INSERT INTO a(hash) VALUES ('bar')")
        con.execute("INSERT INTO a(hash) VALUES ('baz')")
        con.execute("INSERT INTO a(hash) VALUES ('bee')")
        select = "SELECT sn, datetime(ts, 'unixepoch', 'localtime'), hash from a"
        for row in con.execute(select).fetchall():
            print(row)
