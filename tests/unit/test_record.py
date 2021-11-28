import unittest

from mind.mind import Record, Phase, Epoch


class TestRecord(unittest.TestCase):

    def test_default(self):
        # Given / When
        output = Record()
        # Then
        self.assertEqual(output, Record(0, "", 0, output.stamp, Phase.ABSENT,
                                        Phase.HIDDEN))
        self.assertEqual(output.parent(), -1)
        self.assertEqual(output.next(), 1)
        self.assertEqual(output.canonical(), "Record [0,]")

    def test_canonical(self):
        # Given
        hash = "1ab234f"
        # When
        output = Record(1, hash, 0, Epoch.now(), Phase.ABSENT,
                        Phase.HIDDEN).canonical()
        # Then
        self.assertEqual(output, f"Record [1,{hash}]")
