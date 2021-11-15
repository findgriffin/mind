from contextlib import redirect_stdout

import io

from unittest.mock import patch

from tests import setup_context
import unittest

from mind.mind import Mind, add_content, IntegrityError


class TestVerify(unittest.TestCase):
    MEM = ":memory:"

    def setUp(self) -> None:
        self.sesh = setup_context(self, Mind(self.MEM, strict=False))
        self.stdout = setup_context(self, redirect_stdout(io.StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    def test_verify_catch_bad_hash(self):
        # Given
        for i in range(100):
            add_content(self.sesh, ["hello"])
        self.sesh.con.execute("UPDATE log SET hash=:hash WHERE sn=:sn",
                              {"hash": "bad_hash", "sn": 61})
        # When
        with self.assertRaises(IntegrityError):
            self.sesh.verify(40)

    def test_verify_miss_bad_hash(self):
        # Given
        for i in range(100):
            add_content(self.sesh, ["hello"])
        self.sesh.con.execute("UPDATE log SET hash=:hash WHERE sn=:sn",
                              {"hash": "bad_hash", "sn": 60})
        # When
        self.sesh.verify(40)
        # Then no error raised.

    def test_verify_bad_body(self):
        # Given
        for i in range(100):
            add_content(self.sesh, [f"hello{i} #tag{i}"])
        self.sesh.con.execute("UPDATE stuff SET body=:body WHERE body=:orig",
                              {"body": "bad body", "orig": "hello50"})
        # When
        with self.assertRaises(IntegrityError):
            self.sesh.verify()

    def test_verify_bad_state(self):
        # Given
        for i in range(100):
            add_content(self.sesh, [f"hello{i} #tag{i}"])
        self.sesh.con.execute("UPDATE stuff SET state=:state WHERE body=:orig",
                              {"state": 4, "orig": "hello50"})
        # When
        with self.assertRaises(IntegrityError):
            self.sesh.verify()

    def test_verify_bad_tag(self):
        # Given
        for i in range(100):
            add_content(self.sesh, [f"hello{i} #tag{i}"])
        self.sesh.con.execute("UPDATE tags SET tag=:new WHERE tag=:old",
                              {"new": "bad tag", "old": "tag50"})
        # When
        with self.assertRaises(IntegrityError):
            self.sesh.verify()

    def test_verify_missing_tag(self):
        # Given
        for i in range(100):
            add_content(self.sesh, [f"hello{i} #tag{i}"])
        self.sesh.con.execute("DELETE FROM tags WHERE tag=:old",
                              {"old": "tag50"})
        # When
        with self.assertRaises(IntegrityError):
            self.sesh.verify()
