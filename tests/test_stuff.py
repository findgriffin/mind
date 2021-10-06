import unittest

from mind.mind import Epoch, Phase, Stuff, new_stuff

E1 = Epoch(int(1e8))


class TestStuff(unittest.TestCase):

    def test_canonical_active(self):
        # Given
        body = "This discription is longer than fourty characters."
        stuff = Stuff(E1, body, Phase.ACTIVE)
        # When
        output = stuff.canonical()
        # Then
        self.assertEqual(output, f"Stuff [5f5e100,{body}]")

    def test_canonical_inactive(self):
        # Given
        body = "This discription is longer than fourty characters."
        stuff = Stuff(E1, body, Phase.HIDDEN)
        # When
        output = stuff.canonical()
        # Then
        self.assertEqual(output, "Stuff [5f5e100,]")

    def test_repr(self):
        # Given
        body = "This discription is longer than fourty characters."
        # When
        stuff, tags, ts = new_stuff([body], Phase.ACTIVE)
        output = stuff.__repr__()
        # Then
        self.assertEqual(len(output), 78)  # .strip() remove last space
        self.assertEqual(output,
                         f"Stuff[{hex(stuff.id)[2:]},ACTIVE,{body}]")

    def test_human_readable(self):
        # Given
        body = "This discription is longer than fourty characters. Really!"
        # When
        stuff, tags, ts = new_stuff([body], Phase.ACTIVE)
        output = f"{stuff}"
        # Then
        self.assertEqual(len(output), 55)
        self.assertEqual("r than ...", output[-10:])

    def test_human_readable_empty_body(self):
        # Given
        stuff = Stuff(id="123", body=None, state=0)
        # When
        self.assertEqual(stuff.preview(), "EMPTY")
