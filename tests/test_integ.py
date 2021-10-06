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
        self.assertTrue(output[0].endswith("Tags [markdown, nohello]"))

    def verify_old_schema_breaks(self, path):
        # When
        with self.assertRaises(RuntimeError) as context:
            with mind.Mind(path, strict=True) as sesh:
                mind.QueryStuff().execute(sesh)
        # Then
        self.assertIn("Error for table", str(context.exception))
        self.assertIn("Found: ", str(context.exception))

    def test_schema_v1(self):
        self.verify_old_schema_breaks(Path("tests/data/schema-v1.db"))

    def test_schema_v2(self):
        self.verify_old_schema_breaks(Path("tests/data/schema-v2.db"))

    def test_schema_v3(self):
        self.verify_old_schema_breaks(Path("tests/data/schema-v3.db"))

    def test_schema_v4(self):
        self.verify_old_schema_breaks(Path("tests/data/schema-v4.db"))

    def test_schema_v5(self):
        self.verify_old_schema_breaks(Path("tests/data/schema-v5.db"))

    def test_schema_v6(self):
        # Given
        path = Path("tests/data/schema-v6.db")
        # When
        with mind.Mind(path, strict=True) as sesh:
            mind.QueryStuff().execute(sesh)
        # Then
