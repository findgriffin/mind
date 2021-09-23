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
        self.assertFalse(result.stuff)
