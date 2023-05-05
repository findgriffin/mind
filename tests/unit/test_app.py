import unittest

from flask import Flask
from flask_login import encode_cookie
from werkzeug.security import generate_password_hash, check_password_hash

import mind.app
from mind.app import handle_query, User, handle_login, handle_register, \
    handle_stuff, load_user, add_token, serve_login
from mind.mind import Mind


class TestApp(unittest.TestCase):
    app: Flask = None
    MEM = ":memory:"

    def setUp(self) -> None:
        self.app = mind.app.app
        self.app.config['TESTING'] = True
        self.app.config['LOGIN_DISABLED'] = True
        self.app.config['SECRET_KEY'] = 'testing'

    def test_user(self):
        with Flask('test').app_context():
            user = User('davo', generate_password_hash('foo'))
            self.assertTrue(check_password_hash(user.secret, 'foo'))

    def test_empty_query(self):
        with self.app.app_context():
            assert handle_query(Mind(self.MEM), {})

    def test_handle_login(self):
        with self.app.test_request_context():
            assert handle_login()

    def test_load_user(self):
        with self.app.test_request_context():
            self.assertIsNone(load_user('davo'))

    def test_add_token(self):
        with self.app.test_request_context():
            self.assertEqual(64, len(add_token()))

    def test_serve_login(self):
        with self.app.test_request_context():
            self.assertTrue(serve_login())

    def test_handle_register_success(self):
        with self.app.test_request_context(
                data={'user': 'davo', 'password': 'password',
                      'token': encode_cookie('foo', self.app.secret_key)}):
            resp = handle_register()
            self.assertEqual(302, resp.status_code)
            self.assertEqual('/', resp.location)

    def test_handle_register_failure(self):
        with self.app.test_request_context(
                data={'user': 'davo', 'token': 'notavalidtoken',
                      'password': 'password'}):
            resp = handle_register()
            self.assertEqual(302, resp.status_code)

    def test_404(self):
        response = self.app.test_client().get(
            '/somerandomurl')
        self.assertEqual(response.status_code, 302)  # Hmm ?

    def test_query_stuff(self):
        with self.app.test_request_context(
                '/stuff', data='{"query": {}}',
                content_type='application/json'):
            resp = handle_stuff()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, [])

    def test_tick_stuff(self):
        with self.app.test_request_context(
                '/stuff', data='{"tick": {"id": 500, "body": "foo"}}',
                content_type='application/json'):
            resp = handle_stuff()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual({'updated': 'Done: 1970-01-01T00:00 -> foo'},
                             resp.json)

    def test_untick_stuff(self):
        with self.app.test_request_context(
                '/stuff', data='{"untick": {"id": 500, "body": "foo"}}',
                content_type='application/json'):
            resp = handle_stuff()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual({'updated': 'Active: 1970-01-01T00:00 -> foo'},
                             resp.json)

    def test_really_handle_register(self):
        with self.app.test_request_context(
                'register', method="POST", data={
                    'user': 'foo', 'token': 'bar', 'password': 'baz'}):
            self.assertEqual(handle_register().status_code, 302)
