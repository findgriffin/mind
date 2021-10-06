import unittest

from mind.mind import Change, record_or_default, Record, Stuff, Phase, \
    Sequence, Tag


class TestChange(unittest.TestCase):

    def test_first_entry(self):
        # Given
        record = record_or_default(None)
        stuff = Stuff(946684800, "foo", state=Phase.HIDDEN)
        # When
        canon = Change(record, stuff, Phase.ABSENT, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [0,],Stuff [386d4380,HIDDEN,],"
                                "Before [ABSENT],Tags []]")

    def test_add(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                        Phase.ABSENT)
        stuff = Stuff(15, "some body", state=Phase.ACTIVE)
        # When
        canon = Change(parent, stuff, Phase.ABSENT, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,ACTIVE,"
                                "some body],Before [ABSENT],Tags []]")

    def test_add_with_tag(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                        Phase.ABSENT)
        stuff = Stuff(15, "some body", state=Phase.ACTIVE)
        # When
        canon = Change(parent, stuff, Phase.ABSENT, [Tag(1, "1")]).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,ACTIVE,"
                                "some body],Before [ABSENT],Tags [1]]")

    def test_tick(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                        Phase.ABSENT)
        stuff = Stuff(15, "some body", state=Phase.DONE)
        # When
        canon = Change(parent, stuff, Phase.ACTIVE, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,DONE,"
                                "],Before [ACTIVE],Tags []]")
