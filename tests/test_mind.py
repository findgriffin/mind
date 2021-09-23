import unittest
from mind import mind


class TestStub(unittest.TestCase):

    def test_parser(self):
        # Given
        input = ["--name", "Davo"]

        # When
        result = mind.setup(input)

        # Then
        self.assertFalse(result.verbose)
        self.assertEqual(result.name, input[1])

    def test_no_name(self):
        # When
        result = mind.run()

        # Then
        self.assertEqual(result, "Hello, world!")

    def test_name(self):
        # When
        result = mind.run("Davo")

        # Then
        self.assertEqual(result, "Hello, Davo!")
