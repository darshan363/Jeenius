"""End-to-end tests for sign-up, OTP, password reset and teacher <-> learner switching."""
import http.cookiejar
import json
import os
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import server


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class AuthFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = str(Path(cls.tmp.name) / 'auth.sqlite3')
        cls.env = patch.dict(os.environ, {'SQLITE_PATH': cls.db, 'DATABASE_URL': '', 'DEV_SHOW_OTP': '1',
                                          'BREVO_API_KEY': '', 'SMTP_HOST': '', 'SMTP_PASSWORD': ''}, clear=False)
        cls.env.start()
        server.initialize_auth_db()
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.JeeniusHandler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.env.stop()
        cls.tmp.cleanup()

    def client(self):
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), _NoRedirect)

        def call(path, data=None):
            req = urllib.request.Request(f'http://127.0.0.1:{self.port}{path}', method='POST' if data is not None else 'GET',
                                         data=json.dumps(data).encode() if data is not None else None,
                                         headers={'Content-Type': 'application/json'})
            try:
                resp = opener.open(req)
                raw = resp.read()
                return resp.status, (json.loads(raw) if 'json' in resp.headers.get('Content-Type', '') else {})
            except urllib.error.HTTPError as exc:
                raw = exc.read()
                try:
                    return exc.code, json.loads(raw)
                except ValueError:
                    return exc.code, {}
        return call

    def test_signup_otp_profile_and_role_switch(self):
        call = self.client()
        status, body = call('/api/auth/register', {'name': 'Asha', 'email': 'asha@example.com', 'password': 'secret123'})
        self.assertEqual(status, 201)
        code = body['dev_code']
        # Wrong code first, then right code.
        self.assertEqual(call('/api/auth/verify-otp', {'email': 'asha@example.com', 'code': '000000' if code != '000000' else '111111'})[0], 400)
        status, body = call('/api/auth/verify-otp', {'email': 'asha@example.com', 'code': code})
        self.assertEqual((status, body['redirect']), (200, '/account-setup.html'))
        self.assertEqual(call('/api/account/profile', {'name': 'Asha', 'standard': 'multiple', 'account_role': 'learner'})[0], 400)
        self.assertEqual(call('/api/account/profile', {'name': 'Asha', 'standard': '10', 'account_role': 'teacher'})[0], 400)   # Class 10 is out of scope
        self.assertEqual(call('/api/account/profile', {'name': 'Asha', 'standard': 'multiple', 'account_role': 'teacher'})[0], 200)
        # The role is locked: a teacher can neither switch to learner via profile, age step, nor the old role endpoint.
        status, body = call('/api/account/profile', {'name': 'Asha', 'standard': '9', 'account_role': 'learner'})
        self.assertEqual((status, body.get('code')), (403, 'role_locked'))
        self.assertEqual(call('/api/age/declare', {'age': 30, 'account_role': 'learner'})[0], 200)
        self.assertEqual(call('/api/auth/me')[1]['user']['account_role'], 'teacher')
        self.assertEqual(call('/api/account/role', {'account_role': 'learner', 'standard': '9'})[0], 404)

    def test_unfinished_signup_is_recoverable_and_password_not_replaced(self):
        call = self.client()
        self.assertEqual(call('/api/auth/register', {'name': 'Ravi', 'email': 'ravi@example.com', 'password': 'firstpass1'})[0], 201)
        status, body = call('/api/auth/register', {'name': 'Ravi', 'email': 'ravi@example.com', 'password': 'attacker99'})
        self.assertEqual((status, body['code']), (409, 'email_verification_required'))
        status, body = call('/api/auth/login', {'email': 'ravi@example.com', 'password': 'attacker99'})
        self.assertEqual(status, 401)

    def test_forgot_and_reset_password(self):
        call = self.client()
        status, body = call('/api/auth/register', {'name': 'Mina', 'email': 'mina@example.com', 'password': 'oldpass123'})
        call('/api/auth/verify-otp', {'email': 'mina@example.com', 'code': body['dev_code']})
        status, body = call('/api/auth/forgot', {'email': 'mina@example.com'})
        self.assertEqual(status, 200)
        code = body['dev_code']
        self.assertEqual(call('/api/auth/reset', {'email': 'mina@example.com', 'code': code, 'password': 'short'})[0], 400)
        self.assertEqual(call('/api/auth/reset', {'email': 'mina@example.com', 'code': code, 'password': 'newpass123'})[0], 200)
        other = self.client()
        self.assertEqual(other('/api/auth/login', {'email': 'mina@example.com', 'password': 'oldpass123'})[0], 401)
        self.assertEqual(other('/api/auth/login', {'email': 'mina@example.com', 'password': 'newpass123'})[0], 200)

    def test_signup_blocked_clearly_when_email_not_configured(self):
        with patch.dict(os.environ, {'DEV_SHOW_OTP': '0'}):
            status, body = self.client()('/api/auth/register', {'name': 'X', 'email': 'x@example.com', 'password': 'password1'})
        self.assertEqual(status, 503)
        self.assertIn('Google', body['error'])


if __name__ == '__main__':
    unittest.main()
