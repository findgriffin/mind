import datetime
from datetime import datetime
import unittest

from mind.mind import Epoch

class TestEpoch(unittest.TestCase):

    def test_zero(self):
        # Given
        zero = Epoch(0)
        # When
        self.assertEqual(zero, 0)
        self.assertEqual(str(zero), "1970-01-01T00:00")

    def test_now(self):
        # Given
        now = Epoch.now()
        # When
        self.assertGreater(int(datetime.now().timestamp() * 1e6),
                           now)
        self.assertEqual(len(str(now)), 16)

    def test_round_trip(self):
        # Given
        now = Epoch.now()
        # When
        deserialized = Epoch(now)
        # Then
        self.assertEqual(now, deserialized)