from datetime import datetime
from pathlib import Path
from time import sleep
import unittest

from mind import mind

fromiso = datetime.fromisoformat


class TestSQLite(unittest.TestCase):
    MEM = Path(":memory:")

    def test_create_cmd(self):
        # Given
        name = "hello"
        schema = mind.TABLES["stuff"]
        # When
        cmd = mind.create_cmd(name, schema=schema)
        # Then
        self.assertEqual("CREATE TABLE hello(id TEXT NOT NULL PRIMARY KEY, "
                         "body TEXT NOT NULL, state INTEGER NOT NULL)", cmd)

    def test_get_db_inmem(self):
        # Given / When
        with mind.get_db(self.MEM) as con:
            # Then
            self.assertFalse(con.isolation_level)
            self.assertFalse(con.in_transaction)
            cur = con.execute("SELECT * FROM sqlite_master")
            self.assertEqual(cur.fetchone()[-1],
                             "CREATE TABLE stuff(id TEXT NOT NULL PRIMARY KEY,"
                             " body TEXT NOT NULL, state INTEGER NOT NULL)")
        con.close()

    def test_add_and_query(self):
        # Given
        with mind.get_db(self.MEM) as con:
            mind.add(con, ["one", "two", "three"])
            fetched = mind.query_active(con)
            # Then
            self.assertEqual(fetched[0][1], "one two three")
            now = datetime.utcnow()
            # Note: from https://docs.python.org/3/library/datetime.html
            #  > This does not support parsing arbitrary ISO 8601 strings
            #  > - it is only intended as the inverse operation of
            #  > datetime.isoformat()
            # This is good for testing, it makes it a strict test!
            self.assertGreater(now, fromiso(fetched[0][0]))
        con.close()

    def test_add_many_and_query(self):
        with mind.get_db(self.MEM) as con:
            for i in range(20):
                sleep(0.03)
                mind.add(con, f"entry {i}")
            # Then
            fetched = mind.query_active(con)
            self.assertEqual(11, len(fetched))
            self.assertGreater(fromiso(fetched[0][0]),
                               fromiso(fetched[-1][0]))
        con.close()

    def test_update_no_entries(self):
        with mind.get_db(self.MEM) as con:
            mind.add(con, ["some stuff!!"])
            mind.add(con, ["some more stuff!!"])
            active_before = mind.query_active(con)
            self.assertEqual(2, len(active_before))
            mind.update_state(con, 1, mind.State.TICKED)
            active_after = mind.query_active(con)
            self.assertEqual(1, len(active_after))
            self.assertNotIn("more", active_after[0][1])
        con.close()

    def test_display_empty(self):
        with mind.get_db(self.MEM) as con:
            mind.display(con)

    def test_blank_db(self):
        with mind.get_db(Path("tests/data/blank.db")) as con:
            mind.query_active(con)
        con.close()
