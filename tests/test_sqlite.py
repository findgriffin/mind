from argparse import Namespace
from datetime import datetime
from time import sleep
import logging
import random
import string
import unittest


from mind.mind import Mind, QueryStuff, add_content, do_state_change, Phase, \
    QueryTags, do_list, do_forget, do_tick, do_add, do_show


class TestSQLite(unittest.TestCase):
    MEM = ":memory:"

    def test_get_db_inmem(self):
        # Given / When
        with Mind(self.MEM, strict=True) as sesh:
            # Then
            self.assertFalse(sesh.con.isolation_level)
            self.assertFalse(sesh.con.in_transaction)
            cur1 = sesh.con.execute("SELECT * FROM stuff")
            self.assertEqual(cur1.lastrowid, 1)
            cur2 = sesh.con.execute("SELECT * FROM tags")
            self.assertEqual(cur2.lastrowid, 1)

    def test_verify_empty(self):
        logging.basicConfig(level=logging.DEBUG)
        with Mind(self.MEM, strict=True):
            pass
        # Verify on exit

    def test_add_and_query(self):
        # Given
        with Mind(self.MEM, strict=True) as sesh:
            add_content(sesh, ["one"])
            fetched = QueryStuff().execute(sesh)
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
        with Mind(self.MEM, strict=True) as sesh:
            for i in range(20):
                sleep(0.03)
                add_content(sesh, [f"entry {i}"])
            # Then
            fetched = QueryStuff().execute(sesh)
            self.assertEqual(10, len(fetched))
            self.assertGreater(fetched[0][0], fetched[-1][0])

    def test_update_correct_entry(self):
        # Given
        to_tick = "some more stuff!!"
        # When
        with Mind(self.MEM, strict=True) as sesh:
            add_content(sesh, ["some stuff!!"])
            add_content(sesh, [to_tick])
            active_before = QueryStuff().execute(sesh)
            self.assertEqual(2, len(active_before))
            ticked = do_state_change(sesh, ["1"], Phase.DONE)
            active_after = QueryStuff().execute(sesh)
            self.assertIn(to_tick, ticked[0])
            self.assertTrue(ticked[0].startswith("Done: "))
            self.assertEqual(len(ticked), 1)
            self.assertEqual(1, len(active_after))
            self.assertNotIn("more", active_after[0][1])

    def test_add_with_tags(self, strict=True):
        with Mind(self.MEM) as sesh:
            add_content(sesh, ["some stuff!!! #stuff"])
            sleep(.02)
            add_content(sesh, ["more stuff!!! #thing"])
            sleep(.02)
            add_content(sesh, ["less stuff??? #hello"])
            sleep(.02)
            add_content(sesh, ["less stuff??? #thing"])
            latest = QueryTags(id=None).execute(sesh)
            self.assertListEqual([tag.tag for tag in latest],
                                 ["thing", "hello", "stuff"])

    def test_get_lots_of_tags(self):
        # Given
        inserted_tags = 20
        expected_tags = 15
        inserted_rows = 40
        with Mind(self.MEM, strict=True) as sesh:
            for i in range(inserted_rows):
                letters = random.choices(string.ascii_letters, k=11)
                add_content(sesh, [f"{letters} #{i % inserted_tags}"])
                sleep(.005)
            # When
            output = QueryTags(id=None).execute(sesh)
            # Then
            self.assertEqual(len(output), expected_tags)
            for i, tag in enumerate(reversed(output), start=5):
                self.assertEqual(tag.tag, str(i % inserted_tags))

    def test_do_list_empty(self):
        # Given
        with Mind(self.MEM, strict=True) as sesh:
            # When
            output = do_list(sesh, Namespace(cmd=None, num=1000, page=1))
            # Then
            self.assertEqual("  Hmm, couldn't find anything here.", output[2])

    def test_forget_success(self):
        # Given
        args = Namespace(forget=["1"])
        with Mind(self.MEM, strict=True) as sesh:
            add_content(sesh, ["some content"])
            # When
            output = do_forget(sesh, args)
            # Then
            self.assertEqual(1, len(output))
            self.assertTrue(output[0].startswith("Hidden: "))
            self.assertTrue(output[0].endswith(" -> some content"))

    def test_forget_when_empty(self):
        # Given
        args = Namespace(forget=["1"])
        with Mind(self.MEM, strict=True) as sesh:
            # When
            output = do_forget(sesh, args)
            # Then
            self.assertListEqual(["Unable to find stuff: [1]"], output)

    def test_forget_tag_indexed(self):
        # Given
        args = Namespace(forget=["#tag.1"])
        with Mind(self.MEM, strict=True) as sesh:
            # When
            with self.assertRaises(NotImplementedError):
                do_forget(sesh, args)

    def test_tick_multiple_args(self):
        # Given
        args = Namespace(tick=["#tag.1", "wot"])
        with Mind(self.MEM, strict=True) as sesh:
            # When
            with self.assertRaises(NotImplementedError):
                do_tick(sesh, args)

    def test_tick_empty_db(self):
        # Given
        args = Namespace(tick=["1"])
        with Mind(self.MEM, strict=True) as sesh:
            # When
            output = do_tick(sesh, args)
            # Then
            self.assertListEqual(["Unable to find stuff: [1]"], output)

    def test_show_success(self):
        # Given
        args = Namespace(show=["1"])
        with Mind(self.MEM, strict=True) as sesh:
            do_add(sesh, Namespace(text="hello #something"))
            # When
            output = do_show(sesh, args)
            # Then
            self.assertEqual(len(output), 5)
            self.assertTrue("Stuff" in output[0])
            self.assertEqual(output[2], "Tags [something]")
            self.assertEqual(output[4], "hello")

    def test_filtered_list(self):
        # Given
        sep = ":::"
        original_entries = 30
        with Mind(self.MEM, strict=True) as sesh:
            for i in range(original_entries):
                do_add(sesh, Namespace(text=f"Entry{sep}{i+1} #{i % 2}"))
            excluded = []
            for i in range(4):
                excluded.append(do_tick(sesh, Namespace(tick=f"{2}"))[0])
                excluded.append(do_forget(sesh, Namespace(forget=f"{2}"))[0])
            # When
            tag_0 = do_list(sesh, Namespace(list="0", num=10, page=1))
            tag_1 = do_list(sesh, Namespace(list="1", num=10, page=1))

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
