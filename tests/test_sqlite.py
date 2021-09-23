from datetime import datetime
from pathlib import Path
from time import sleep
import unittest

from mind import mind
fromiso = datetime.fromisoformat


class TestSQLite(unittest.TestCase):
    MEM = Path(":memory:")

    def test_get_db_inmem(self):
        # Given / When
        with mind.get_db(self.MEM) as con:
            # Then
            self.assertFalse(con.isolation_level)
            self.assertFalse(con.in_transaction)
            cur = con.execute("SELECT * FROM sqlite_master")
            self.assertEqual(cur.fetchone()[-1],
                             "CREATE TABLE stuff(id TEXT PRIMARY KEY,"
                             "body TEXT NOT NULL,state INTEGER NOT NULL)")

    def test_add_and_query(self):
        # Given
        with mind.get_db(self.MEM) as con:
            mind.add(con, ["one", "two", "three"])
            fetched = mind.query(con)
            # Then
            self.assertEqual(fetched[0][1], "one two three")
            now = datetime.utcnow()
            # Note: from https://docs.python.org/3/library/datetime.html
            #  > This does not support parsing arbitrary ISO 8601 strings
            #  > - it is only intended as the inverse operation of
            #  > datetime.isoformat()
            # This is good for testing, it makes it a strict test!
            self.assertGreater(now, fromiso(fetched[0][0]))

    def test_add_many_and_query(self):
        with mind.get_db(self.MEM) as con:
            for i in range(20):
                sleep(0.03)
                mind.add(con, f"entry {i}")
            # Then
            fetched = mind.query(con)
            self.assertEqual(11, len(fetched))
            self.assertGreater(fromiso(fetched[0][0]),
                               fromiso(fetched[-1][0]))
