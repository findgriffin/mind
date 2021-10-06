""" Test the 'Light Relational Model' (lighter than an ORM) """
import unittest

from mind import mind


class TestLRM(unittest.TestCase):

    def test_insert(self):
        rcd = mind.Record(0, "", 0, mind.Phase.ABSENT)
        stmt = mind.insert("foo", rcd)
        self.assertEqual(stmt, "INSERT INTO foo (sn, hash, stuff, before) "
                         "VALUES (:sn, :hash, :stuff, :before)")

    def test_insert_even_if_none(self):
        rcd = mind.Record(0, None, None, None)
        stmt = mind.insert("foo", rcd)
        self.assertEqual(stmt, "INSERT INTO foo (sn, hash, stuff, before) "
                               "VALUES (:sn, :hash, :stuff, :before)")
