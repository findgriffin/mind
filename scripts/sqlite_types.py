#! /usr/bin/env python3

# From https://docs.python.org/3/library/sqlite3.html
#   #converting-sqlite-values-to-custom-python-types
import sqlite3
from enum import IntEnum

State = IntEnum("State", "ACTIVE PASSIVE DONE")

class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return "(%f;%f)" % (self.x, self.y)

def adapt_point(point):
    return ("%f;%f" % (point.x, point.y)).encode('ascii')

def convert_point(s):
    x, y = list(map(float, s.split(b";")))
    return Point(x, y)

# Register the adapter
sqlite3.register_adapter(Point, adapt_point)
sqlite3.register_adapter(State, lambda s: s.value)

# Register the converter
sqlite3.register_converter("point", convert_point)
sqlite3.register_converter("state", lambda b: State(int(b)))

p = Point(4.0, -3.2)
s = State(2) # PASSIVE

#########################
# 1) Using declared types
con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
cur = con.cursor()
cur.execute("create table test(p point, s state)")

cur.execute("insert into test(p,s) values (?,?)", (p,s))
cur.execute("select p,s from test")
print("with declared types:", cur.fetchone())
cur.close()
con.close()

#######################
# 1) Using column names
con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_COLNAMES)
cur = con.cursor()
cur.execute("create table test(p,s)")

cur.execute("insert into test(p,s) values (?,?)", (p,s))

cur.execute('select p as "p [point]" from test')
print("Point with column names:", cur.fetchone()[0])
cur.execute('select s as "s [state]" from test')
print("State with column names:", cur.fetchone()[0])
cur.close()
con.close()

# 2) Test check constraints
