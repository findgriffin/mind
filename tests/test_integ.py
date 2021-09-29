import logging
import unittest
from argparse import Namespace

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
