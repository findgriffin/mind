import unittest
from mind import mind


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
        input = ["add", "my", "little", "pony"]
        # When
        result = mind.setup(input)
        # Then
        self.assertListEqual(result.add, input[1:])
