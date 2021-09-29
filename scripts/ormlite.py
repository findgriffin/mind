#! /usr/bin/env python3
import sqlite3
# From https://docs.python.org/3/library/sqlite3.html

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
#create_and_insert()
select()
parameterized()