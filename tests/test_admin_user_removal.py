"""Regression tests for safe admin removal of regular JEENIUS accounts."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server


class AdminUserRemovalTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tempdir.name) / 'users.sqlite3')
        self.env_patch = patch.dict(os.environ, {
            'SQLITE_PATH': self.path,
            'DATABASE_URL': '',
            'ADMIN_EMAILS': 'admin@example.com',
        }, clear=False)
        self.env_patch.start()
        server.initialize_auth_db()
        conn = server._db_connect()
        try:
            conn.execute("INSERT INTO users(id,email,name,created_at,updated_at,email_verified) VALUES (?,?,?,?,?,1)",
                         ('regular-user', 'student@example.com', 'Student', 1, 1))
            conn.execute("INSERT INTO users(id,email,name,created_at,updated_at,email_verified) VALUES (?,?,?,?,?,1)",
                         ('admin-user', 'admin@example.com', 'Admin', 1, 1))
            conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                         ('session-hash', 'regular-user', 9999999999, 1))
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        self.env_patch.stop()
        self.tempdir.cleanup()

    def _handler(self, acting_admin, body):
        handler = server.JeeniusHandler.__new__(server.JeeniusHandler)
        response = {}
        handler._require_session_user = lambda: acting_admin
        handler._read_json_body = lambda: body
        handler._send_json = lambda status, payload, headers=None: response.update(status=status, payload=payload)
        handler._admin_remove_user()
        return response

    def test_admin_can_remove_regular_user_and_revoke_sessions(self):
        out = self._handler({'id': 'admin-user', 'email': 'admin@example.com'}, {'user_id': 'regular-user'})
        self.assertEqual(out['status'], 200)
        conn = server._db_connect()
        try:
            self.assertIsNone(conn.execute('SELECT id FROM users WHERE id = ?', ('regular-user',)).fetchone())
            self.assertIsNone(conn.execute('SELECT token_hash FROM auth_sessions WHERE token_hash = ?', ('session-hash',)).fetchone())
        finally:
            conn.close()

    def test_admin_accounts_are_protected(self):
        out = self._handler({'id': 'regular-user', 'email': 'admin@example.com'}, {'user_id': 'admin-user'})
        self.assertEqual(out['status'], 403)
        conn = server._db_connect()
        try:
            self.assertIsNotNone(conn.execute('SELECT id FROM users WHERE id = ?', ('admin-user',)).fetchone())
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
