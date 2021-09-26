import unittest

from mind import mind


class TestStuff(unittest.TestCase):

    def test_repr(self):
        # Given
        body = "This discription is longer than fourty characters."
        # When
        stuff, tags = mind.new_stuff([body])
        output = stuff.__repr__()
        # Then
        self.assertEqual(len(output), 59)  # .strip() remove last space
        self.assertEqual("ion is...]", output[-10:])

    def test_human_readable(self):
        # Given
        body = "This discription is longer than fourty characters. Really!"
        # When
        stuff, tags = mind.new_stuff([body])
        output = f"{stuff}"
        # Then
        self.assertEqual(len(output), 63)
        self.assertEqual("ourty c...", output[-10:])
