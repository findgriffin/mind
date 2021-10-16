import logging
import unittest
from argparse import Namespace
from pathlib import Path

from mind import mind


class TestInteg(unittest.TestCase):
    """ Test components at higher level, to check that things work together."""
    MEM = ":memory:"
    LATEST_SCHEMA = 8

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

    def test_old_schemas(self):
        for i in range(1, self.LATEST_SCHEMA - 1):
            path = Path(f"tests/data/schema-v{i}.db")
            with self.subTest(f"Testing old schema: {path}"):
                # When
                with self.assertRaises(RuntimeError) as context:
                    with mind.Mind(path, strict=True) as sesh:
                        mind.QueryStuff().execute(sesh)
                # Then
                self.assertIn("Error for table", str(context.exception))
                self.assertIn("Found: ", str(context.exception))

    def test_latest_schema(self):
        # Given
        path = Path(f"tests/data/schema-v{self.LATEST_SCHEMA}.db")
        # When
        with mind.Mind(path, strict=True):
            pass
        # Then verify on exit
