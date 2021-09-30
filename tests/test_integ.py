import logging
import unittest
from argparse import Namespace
from pathlib import Path

from mind import mind


class TestInteg(unittest.TestCase):
    """ Test components at higher level, to check that things work together."""
    MEM = ":memory:"

    def test_logging_setup(self):
        # Given
        with self.assertLogs(level=logging.DEBUG) as root:
            # When
            mind.setup_logging(verbose=False)
        # Then
        self.assertListEqual(root.output,
                             ["DEBUG:root:Verbose logging enabled."])

    def test_run_method(self):
        # Given
        args = Namespace(db=self.MEM, cmd="add",
                         text=None, interactive=None,
                         file="tests/data/note.md")
        # When
        output = mind.run(args)
        # Then
        self.assertEqual(1, len(output))
        self.assertTrue(output[0].startswith("Added "))
        self.assertIn(" -> # This is how you Markdown", output[0])
        self.assertTrue(output[0].endswith("tags[markdown, nohello]"))

    def test_schema_v1(self):
        # Given
        path = Path("tests/data/schema-v1.db")
        # When
        with self.assertRaises(RuntimeError) as context:
            with mind.get_db(path, strict=True) as con:
                mind.QueryStuff().execute(con)
            con.close()
        # Then
        self.assertIn("Error for table", str(context.exception))
        self.assertIn("Found: ", str(context.exception))

    def test_schema_v2(self):
        # Given
        path = Path("tests/data/schema-v2.db")
        # When
        with self.assertRaises(RuntimeError) as context:
            with mind.get_db(path, strict=True) as con:
                mind.QueryStuff().execute(con)
            con.close()
        # Then
        self.assertIn("Error for table", str(context.exception))
        self.assertIn("Found: ", str(context.exception))

    def test_schema_v3(self):
        # Given
        path = Path("tests/data/schema-v3.db")
        # When
        with mind.get_db(path, strict=True) as con:
            mind.QueryStuff().execute(con)
        # Then
        con.close()
