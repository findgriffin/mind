from argparse import Namespace
from datetime import datetime

from contextlib import redirect_stdout

import io
from time import sleep
import logging
import random
import string
import unittest

from unittest.mock import patch

from mind.mind import Mind, QueryStuff, add_content, \
    QueryTags, do_list, do_forget, do_tick, do_add, do_show
from tests import setup_context


class TestSQLite(unittest.TestCase):
    MEM = ":memory:"

    def setUp(self) -> None:
        self.sesh = setup_context(self, Mind(self.MEM, strict=True))
        self.stdout = setup_context(self, redirect_stdout(io.StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    def test_get_db_inmem(self):
        # Given / When
        # Then
        self.assertFalse(self.sesh.con.isolation_level)
        self.assertFalse(self.sesh.con.in_transaction)
        cur1 = self.sesh.con.execute("SELECT * FROM stuff")
        self.assertEqual(cur1.lastrowid, 1)
        cur2 = self.sesh.con.execute("SELECT * FROM tags")
        self.assertEqual(cur2.lastrowid, 1)

    def test_verify_empty(self):
        logging.basicConfig(level=logging.DEBUG)
        with Mind(self.MEM, strict=True):
            pass
        # Verify on exit

    def test_add_and_query(self):
        # Given
        add_content(self.sesh, ["one"])
        fetched = QueryStuff().fetchall(self.sesh)
        # Then
        self.assertEqual(fetched[0][1], "one")
        now = datetime.utcnow().timestamp()
        # Note: from https://docs.python.org/3/library/datetime.html
        #  > This does not support parsing arbitrary ISO 8601 strings
        #  > - it is only intended as the inverse operation of
        #  > datetime.isoformat()
        # This is good for testing, it makes it a strict test!
        self.assertGreater(now * 1e6, fetched[0].id)

    def test_add_many_and_query(self):
        for i in range(20):
            sleep(0.03)
            add_content(self.sesh, [f"entry {i}"])
        # Then
        fetched = QueryStuff().fetchall(self.sesh)
        self.assertEqual(10, len(fetched))
        self.assertGreater(fetched[0][0], fetched[-1][0])

    def test_update_correct_entry(self):
        # Given
        to_tick = "some more stuff!!"
        # When
        add_content(self.sesh, ["some stuff!!"])
        add_content(self.sesh, [to_tick])
        active_before = QueryStuff().fetchall(self.sesh)
        self.assertEqual(2, len(active_before))
        ticked = do_tick(self.sesh, Namespace(tick="1"))
        active_after = QueryStuff().fetchall(self.sesh)
        self.assertIn(to_tick, ticked[0])
        self.assertTrue(ticked[0].startswith("Done: "))
        self.assertEqual(len(ticked), 1)
        self.assertEqual(1, len(active_after))
        self.assertNotIn("more", active_after[0][1])

    def test_add_with_tags(self, strict=True):
        add_content(self.sesh, ["some stuff!!! #stuff"])
        sleep(.02)
        add_content(self.sesh, ["more stuff!!! #thing"])
        sleep(.02)
        add_content(self.sesh, ["less stuff??? #hello"])
        sleep(.02)
        add_content(self.sesh, ["less stuff??? #thing"])
        latest = QueryTags(id=None).execute(self.sesh)
        self.assertListEqual([tag.tag for tag in latest],
                             ["thing", "hello", "stuff"])

    def test_get_lots_of_tags(self):
        # Given
        inserted_tags = 20
        expected_tags = 15
        inserted_rows = 40
        for i in range(inserted_rows):
            letters = random.choices(string.ascii_letters, k=11)
            add_content(self.sesh, [f"{letters} #{i % inserted_tags}"])
            sleep(.005)
        # When
        output = QueryTags(id=None).execute(self.sesh)
        # Then
        self.assertEqual(len(output), expected_tags)
        for i, tag in enumerate(reversed(output), start=5):
            self.assertEqual(tag.tag, str(i % inserted_tags))

    def test_do_list_empty(self):
        # Given
        # When
        output = do_list(self.sesh, Namespace(cmd=None, num=1000, page=1))
        # Then
        self.assertEqual("  Hmm, couldn't find anything here.", output[2])

    def test_forget_success(self):
        # Given
        args = Namespace(forget="1")
        add_content(self.sesh, ["some content"])
        # When
        output = do_forget(self.sesh, args)
        # Then
        self.assertEqual(1, len(output))
        self.assertTrue(output[0].startswith("Hidden: "))
        self.assertTrue(output[0].endswith(" -> some content"))

    def test_forget_when_empty(self):
        # Given
        args = Namespace(forget="1")
        # When
        output = do_forget(self.sesh, args)
        # Then
        self.assertListEqual(["Stuff with ID 1 not found."], output)

    def test_forget_tag_indexed(self):
        # Given
        args = Namespace(forget="#tag.1")
        # When
        with self.assertRaises(ValueError):
            do_forget(self.sesh, args)

    def test_tick_multiple_args(self):
        # Given
        args = Namespace(tick="1,2,3")
        # When
        do_add(self.sesh, Namespace(text="one"))
        do_add(self.sesh, Namespace(text="two"))
        do_add(self.sesh, Namespace(text="three"))
        ticked = do_tick(self.sesh, args)

        # Then
        listed = do_list(self.sesh, Namespace(num=10, page=1))
        self.assertEqual(len(ticked), 3)
        self.assertIn("  Hmm, couldn't find anything here.", listed)

    def test_tick_empty_db(self):
        # Given
        args = Namespace(tick="1")
        # When
        output = do_tick(self.sesh, args)
        # Then
        self.assertListEqual(["Stuff with ID 1 not found."], output)

    def test_show_success(self):
        # Given
        args = Namespace(show="1")
        do_add(self.sesh, Namespace(text="hello #something"))
        # When
        output = do_show(self.sesh, args)
        # Then
        self.assertEqual(len(output), 5)
        self.assertTrue("Stuff" in output[0])
        self.assertEqual(output[2], "Tags [something]")
        self.assertEqual(output[4], "hello")

    def test_filtered_list(self):
        # Given
        sep = ":::"
        original_entries = 30
        for i in range(original_entries):
            do_add(self.sesh, Namespace(text=f"Entry{sep}{i+1} #{i % 2}"))
        excluded = []
        for i in range(4):
            excluded.append(do_tick(self.sesh, Namespace(tick=f"{2}"))[0])
            excluded.append(do_forget(self.sesh,
                                      Namespace(forget=f"{2}"))[0])
        # When
        tag_0 = do_list(self.sesh, Namespace(list="0", num=10, page=1))
        tag_1 = do_list(self.sesh, Namespace(list="1", num=10, page=1))

        excluded_set = set([text.split(sep)[-1] for text in excluded])
        tag_0_set = set([text.split(sep)[-1] for text in tag_0[2:-4]])
        tag_1_set = set([text.split(sep)[-1] for text in tag_1[2:-4]])

        self.assertSetEqual(set(excluded_set) & set(tag_0_set), set())
        self.assertSetEqual(set(excluded_set) & set(tag_1_set), set())
        self.assertSetEqual(set(tag_0_set) & set(tag_1_set), set())

        union = excluded_set.union(tag_0_set).union(tag_1_set)
        self.assertEqual(len(tag_0_set), 10)
        self.assertEqual(len(tag_1_set), 10)
        self.assertEqual(len(union), 28)
