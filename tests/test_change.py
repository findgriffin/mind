import unittest

from mind.mind import Change, record_or_default, Record, Stuff, Phase, \
    Sequence, Tag, Epoch

E1 = Epoch(1)
E2 = Epoch(2)
PARENT = Record(Sequence(30), "hash", 23, E1, Phase.ABSENT, Phase.ACTIVE)
PHASES = (Phase.ABSENT, Phase.ACTIVE)

class TestChange(unittest.TestCase):

    def test_first_entry(self):
        # Given
        record = record_or_default(None)
        stuff = Stuff(Epoch(946684800), "", state=Phase.HIDDEN)
        # When
        canon = Change(record, stuff, (Phase.ABSENT, Phase.HIDDEN),
                       E1, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [0,],Stuff [386d4380,],"
                                "Phases [ABSENT->HIDDEN],Tags []]")

    def test_add(self):
        # Given
        stuff = Stuff(Epoch(15), "some body", state=Phase.ACTIVE)
        # When
        canon = Change(PARENT, stuff, PHASES, E2, []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,"
                                "some body],Phases [ABSENT->ACTIVE],Tags []]")

    def test_add_with_tag(self):
        # Given
        stuff = Stuff(Epoch(15), "some body", state=Phase.ACTIVE)
        tags = [Tag(1, "1"), Tag(1, "2")]
        # When
        change = Change(PARENT, stuff, PHASES, E2, tags)
        # Then
        self.assertEqual(change.canonical(),
                         "Change [Record [30,hash],Stuff [f,some "\
                         "body],Phases [ABSENT->ACTIVE],Tags [1, 2]]")

    def test_tick(self):
        # Given
        stuff = Stuff(Epoch(15), "some body", state=Phase.DONE)
        # When
        canon = Change(PARENT, stuff,
                       (Phase.ACTIVE, Phase.DONE), Epoch(11), []).canonical()
        # Then
        self.assertEqual(canon, "Change [Record [30,hash],Stuff [f,"
                                "],Phases [ACTIVE->DONE],Tags []]")
