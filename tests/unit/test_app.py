import unittest

from mind.app import handle_query, User, app
from mind.mind import Mind

class TestApp(unittest.TestCase):
    MEM = ":memory:"

    def test_user(self):
        user = User(name='davo')
        self.assertFalse(user.set_password('hello'))
        self.assertTrue(user.check_password('hello'))

    def test_empty_query(self):
        assert handle_query(Mind(self.MEM), '{}')


