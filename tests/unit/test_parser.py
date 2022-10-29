import unittest
from io import StringIO
from unittest.mock import patch

from mind import cli as mind


class TestParser(unittest.TestCase):

    def test_parser_no_args(self):
        # Given
        input = []
        # When
        result = mind.setup(input)
        # Then
        self.assertFalse(result.verbose)

    def test_parser_add(self):
        # Given
        input = ["add", "-t", "my little pony"]
        # When
        result = mind.setup(input)
        # Then
        self.assertEqual(result.cmd, input[0])

    @patch('sys.stderr', new_callable=StringIO)
    def test_parser_add_too_many(self, mock_stderr):
        # Given
        input = ["add", "my", "little", "pony"]
        # When
        with self.assertRaises(SystemExit) as context:
            mind.setup(input)

        self.assertEqual(2, context.exception.code)
        self.assertTrue("unrecognized arguments" in mock_stderr.getvalue())

    def test_add_file(self):
        # Given
        input = ["add", "--file",  "foo.txt"]
        # When
        result = mind.setup(input)
        # Then
        self.assertEqual(result.cmd, input[0])
        self.assertEqual(result.file, input[2])
