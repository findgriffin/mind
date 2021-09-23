from pathlib import Path

from mind import mind
import unittest


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

    def test_con_stays_open(self):
        # Given
        with mind.get_db(self.MEM) as con:
            mind.display(con)
        # When
        cur = con.execute("SELECT * FROM stuff")
        # Then
        self.assertTrue(cur)
