#! /usr/bin/env python3
import datetime
import sqlite3
# From https://docs.python.org/3/library/sqlite3.html
from sqlite3 import Row, Cursor
from typing import NamedTuple, Optional


def create_and_insert():
    con = sqlite3.connect('example.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE stocks (date text, trans text,
                   symbol text, qty real, price real)''')
    cur.execute(
        "INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")
    con.commit()
    con.close()

def select():
    con = sqlite3.connect('example.db')
    cur = con.cursor()
    for row in cur.execute('SELECT * FROM stocks ORDER BY price'):
        print(row)

def parameterized():

    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("create table lang (name, first_appeared)")

    cur.execute("insert into lang values (?, ?)", ("C", 1972))

    lang_list = [
        ("Fortran", 1957),
        ("Python", 1991),
        ("Go", 2009),
    ]
    cur.executemany("insert into lang values (?, ?)", lang_list)

    # And this is the named style:
    cur.execute("select * from lang where first_appeared=:year",
                {"year": 1972})
    print(cur.fetchall())
    con.close()



class DBCon():

    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        print(self.con.isolation_level)

    def tx(self, stmt, params=()) -> Cursor:
        with self.con:
            cur = self.con.execute(stmt, params)
            return cur

    def query(self, stmt, params=()) -> Cursor:
        return self.con.execute(stmt, params).fetchall()

class Log():
    name = "log"
    def __init__(self, con: DBCon):
        self.con = con
        con.tx("CREATE TABLE IF NOT EXISTS log("
               "sn INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
               "ts INT NOT NULL DEFAULT (cast(strftime('%s', 'now') as INT)),"
               "body TEXT NOT NULL)")

    def append(self, body):
        cur = self.con.tx("INSERT INTO log(body) VALUES (?)", (body,))
        print(f"Appended {cur.lastrowid}")

    def query(self, fields = None):
        self.con.query()


def commit_log():
    con = DBCon("log.db")
    log = Log(con)
    log.append("Helloooo!")

    for row in con.query("SELECT * FROM log ORDER BY sn DESC"):
        print(row[:])
    for row in con.query("SELECT * FROM log WHERE sn = :num", {"num": 6}):
        print("Rows are great!")
        #print(f"{row[0]} {row[1]} {row['body']}")
        print(f"{tuple(row)}")
        print(f"{dict(row)}")
    for row in con.query("SELECT * FROM log ORDER BY sn DESC LIMIT 1"):
        print(row)

def sequence_number_enforcement():
    a_inc = "INTEGER PRIMARY KEY AUTOINCREMENT"
    check = "CHECK (sn > 0)"
    con = sqlite3.connect(":memory:")
    t1 = con.execute(f"CREATE TABLE t1(sn {a_inc}, b TEXT)")
    t2 = con.execute(f"CREATE TABLE t2(sn {a_inc} {check}, b TEXT)")
    for i in range(10):
        with con:
            con.execute(f"INSERT INTO t1 (b) VALUES ('Entry {i}')")
            con.execute(f"INSERT INTO t2 (b) VALUES ('Entry {i}')")
    # Leave a gap
    with con:
        con.execute(f"INSERT INTO t1 (sn, b) VALUES (15, 'Entry 15')")
        con.execute(f"INSERT INTO t2 (sn, b) VALUES (15, 'Entry 15')")

    # Now insert taking advantage of autoincrement
    with con:
        cur1 = con.execute(f"INSERT INTO t1 (b) VALUES ('Entry 16')")
        print(f" t1 sn: {cur1.lastrowid}")
        cur2 = con.execute(f"INSERT INTO t2 (b) VALUES ('Entry 16')")
        print(f" t2 sn: {cur2.lastrowid}")

    # Now insert in the gap between lastrowid and 10
    with con:
        cur1 = con.execute(f"INSERT INTO t1 (sn, b) VALUES (11, 'Entry 17')")
        print(f" t1 sn: {cur1.lastrowid}")
        cur2 = con.execute(f"INSERT INTO t2 (sn, b) VALUES (11, 'Entry 17')")
        print(f" t2 sn: {cur2.lastrowid}")

    # Now insert again using autoincrement
    with con:
        cur1 = con.execute(f"INSERT INTO t1 (b) VALUES ('Entry 18')")
        print(f" t1 sn: {cur1.lastrowid}")
        cur2 = con.execute(f"INSERT INTO t2 (b) VALUES ('Entry 18')")
        print(f" t2 sn: {cur2.lastrowid}")

    # Now insert failing check constraint
    with con:
        cur1 = con.execute(f"INSERT INTO t1 (sn, b) VALUES (-1, 'Entry 19')")
        print(f" t1 sn: {cur1.lastrowid}")
        cur2 = con.execute(f"INSERT INTO t2 (sn, b) VALUES (-1, 'Entry 19')")
        print(f" t2 sn: {cur2.lastrowid}")
def ideal_commit_log():
    pass
    #  = connect("log.db")
#create_and_insert()
#select()
#parameterized()
#commit_log()
sequence_number_enforcement()
