import unittest
from mind import mind

class TestRecord(unittest.TestCase):

    def test_default(self):
        # Given
        row = None
        # When
        output = mind.record_or_default(None)
        # Then
        self.assertEqual(output, mind.Record(0, "", 0, output.stamp,
                                             mind.Phase.ABSENT))
        self.assertEqual(output.parent(), -1)
        self.assertEqual(output.next(), 1)
        self.assertEqual(output.canonical(), "Record [0,]")

    def test_canonical(self):
        # Given
        hash = "1ab234f"
        # When
        output = mind.Record(1, hash, 0, mind.Epoch.now(),
                             mind.Phase.ABSENT).canonical()
        # Then
        self.assertEqual(output, f"Record [1,{hash}]")
