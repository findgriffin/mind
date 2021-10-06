""" Test the 'Light Relational Model' (lighter than an ORM) """
import unittest

from mind import mind

INSERT_FOO = "INSERT INTO foo (sn, hash, stuff, stamp, old_state, new_state)" \
             " VALUES (:sn, :hash, :stuff, :stamp, :old_state, :new_state)"

class TestLRM(unittest.TestCase):


    def test_insert(self):
        rcd = mind.Record(0, "", 0, mind.Epoch.now(), mind.Phase.ABSENT,
                          mind.Phase.ACTIVE)
        stmt = mind.insert("foo", rcd)
        self.assertEqual(stmt, INSERT_FOO)

    def test_insert_even_if_none(self):
        rcd = mind.Record(0, None, None, None, None, None)
        stmt = mind.insert("foo", rcd)
        self.assertEqual(stmt, INSERT_FOO)
