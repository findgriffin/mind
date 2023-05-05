import unittest

from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash

from mind.app import handle_query, User
from mind.mind import Mind


class TestApp(unittest.TestCase):
    MEM = ":memory:"

    def test_user(self):
        with Flask('test').app_context():
            user = User('davo', generate_password_hash('foo'))
            self.assertTrue(check_password_hash(user.secret, 'foo'))

    def test_empty_query(self):
        with Flask('test').app_context():
            assert handle_query(Mind(self.MEM), {})
