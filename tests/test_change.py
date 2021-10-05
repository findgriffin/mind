import unittest

from mind.mind import Change, record_or_default, Record, Stuff, State, \
    Sequence, Tag


class TestChange(unittest.TestCase):

    def test_first_entry(self):
        # Given
        record = record_or_default(None)
        stuff = Stuff(946684800, "foo", state=State.HIDDEN)
        # When
        canon = Change(record, stuff, State.ABSENT, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [0,],Stuff [386d4380,HIDDEN,],"
                                "Before [ABSENT],Tags []]")

    def test_add(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                             State.ABSENT)
        stuff = Stuff(15, "some body", state=State.ACTIVE)
        # When
        canon = Change(parent, stuff, State.ABSENT, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,ACTIVE,"
                                "some body],Before [ABSENT],Tags []]")

    def test_add_with_tag(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                        State.ABSENT)
        stuff = Stuff(15, "some body", state=State.ACTIVE)
        # When
        canon = Change(parent, stuff, State.ABSENT, [Tag(1,"1")]).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,ACTIVE,"
                                "some body],Before [ABSENT],Tags [1]]")

    def test_tick(self):
        # Given
        parent = Record(Sequence(30), "hash", 23,
                        State.ABSENT)
        stuff = Stuff(15, "some body", state=State.DONE)
        # When
        canon = Change(parent, stuff, State.ACTIVE, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,DONE,"
                                "],Before [ACTIVE],Tags []]")
