from unittest import TestCase


class TestTest(TestCase):
    """Seems like I was attempting to validate behaviour of unittest here?"""

    def test_list_classic(self):
        first = [1, 2, 3, 4]
        second = [4, 3, 2, 1]

        assert set(first) == set(second)
        assert sorted(first) == sorted(second)
        with self.assertRaises(AssertionError):
            assert first == second

    def test_list_modern(self):
        first = [1, 2, 3, 4]
        second = [4, 3, 2, 1]
        self.assertSetEqual(set(first), set(second))
        with self.assertRaises(AssertionError):
            self.assertListEqual(first, second)

    def test_set_classic(self):
        first = {1, 2, 3, 4}
        second = {4, 3, 2, 1}
        assert first == second

    def test_set_modern(self):
        first = {1, 2, 3, 4}
        second = {4, 3, 2, 1}
        self.assertSetEqual(first, second)

    def test_dict_classic(self):
        first = {1: 2, 3: 4}
        second = {3: 4, 1: 2}
        assert first == second

    def test_dict_modern(self):
        first = {1: 2}
        first[3] = 4
        second = {3: 4}
        second[1] = 2
        self.assertDictEqual(first, second)
