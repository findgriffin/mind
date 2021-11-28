from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
import io
import logging
import unittest

from unittest.mock import patch

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

    def test_help(self):
        # Given
        argv = ['-h']
        # When
        with redirect_stdout(io.StringIO()) as stdout_buffer:
            with self.assertRaises(SystemExit) as exit:
                mind.setup(argv)
        stdout = stdout_buffer.getvalue()

        # Then
        self.assertEqual(exit.exception.code, 0)
        self.assertIn("Hello!", stdout)
        self.assertIn("positional arguments:", stdout)
        self.assertIn("-h, --help", stdout)
        self.assertIn("-v, --verbose", stdout)

    def test_no_args(self):
        # Given
        argv = []
        # When
        output = mind.main(argv)
        # Then
        self.assertEqual(output[0],
                         " # Currently minding [latest] [ALL] [num=9]...")
        self.assertEqual(output[-3], "-" * 80)
        self.assertEqual(output[-2][:14], "  Latest tags:")
        self.assertEqual(output[-1], "-" * 80)

    def test_add_interactive(self):
        # Given
        argv = ["--db", self.MEM, "add"]
        test_input = "Some stuff here"
        with patch("builtins.input", return_value=test_input):
            # When
            output = mind.main(argv)
        # Then
        self.assertEqual(output[0][-27:], f" -> {test_input} Tags []")

    def test_old_schemas(self):
        for i in range(1, 6):
            path = Path(f"tests/data/schema-v{i}.db")
            with self.subTest(f"Testing old schema: {path}"):
                # When
                with self.assertRaises(mind.IntegrityError):
                    with mind.Mind(path, strict=True) as sesh:
                        mind.QueryStuff().fetchall(sesh)

    def test_latest_schema(self):
        # Given
        path = Path("tests/data/schema-v7.db")
        # When
        with mind.Mind(path, strict=True):
            pass
        # Then verify on exit
