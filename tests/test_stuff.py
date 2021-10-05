import unittest

from mind import mind


class TestStuff(unittest.TestCase):

    def test_repr(self):
        # Given
        body = "This discription is longer than fourty characters."
        # When
        stuff, tags = mind.new_stuff([body], mind.State.ACTIVE)
        output = stuff.__repr__()
        # Then
        self.assertEqual(len(output), 78)  # .strip() remove last space
        self.assertEqual(output,
                         f"Stuff[{hex(stuff.id)[2:]},ACTIVE,{body}]")

    def test_human_readable(self):
        # Given
        body = "This discription is longer than fourty characters. Really!"
        # When
        stuff, tags = mind.new_stuff([body], mind.State.ACTIVE)
        output = f"{stuff}"
        # Then
        self.assertEqual(len(output), 55)
        self.assertEqual("r than ...", output[-10:])

    def test_human_readable_empty_body(self):
        # Given
        stuff = mind.Stuff(id="123", body=None, state=0)
        # When
        self.assertEqual(stuff.preview(), "EMPTY")
