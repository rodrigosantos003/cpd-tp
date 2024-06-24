"""
 Tests the application API

"""

import base64
import unittest

from app import app, db


def auth_header(username, password):
    """Returns the authorization header."""
    credentials = f'{username}:{password}'
    b64credentials = base64.b64encode(credentials.encode()).decode('utf-8')
    return {'Authorization': f'Basic {b64credentials}'}


class TestBase(unittest.TestCase):
    """Base for all tests."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db = db
        self.db.recreate()

    def tearDown(self):
        pass


class TestUsers(TestBase):
    """Tests for the user endpoints."""

    def setUp(self):
        super().setUp()

    def test_correct_credentials(self):
        """Tests the user with correct credentials."""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/user/', headers=credentials)
        self.assertEqual(res.status_code, 200)

    def test_wrong_credentials(self):
        """Tests the user with incorrect credentials."""
        credentials = auth_header('no-user', 'no-password')
        res = self.client.get('/api/user/', headers=credentials)
        self.assertEqual(res.status_code, 403)

    def test_user_register(self):
        """Tests user registration"""
        response = self.client.post('/api/user/register/', data=dict(
            name='John Doe',
            email='john@example.com',
            username='johndoe',
            password='password123'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn('User registered successfully', response.get_json()['success'])

    def test_user_detail(self):
        """Tests user detail"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/user/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('homer', res.get_json()['username'])

    def test_user_update(self):
        credentials = auth_header('homer', '1234')
        res = self.client.put('/api/user/', headers=credentials, data=dict(
            name='Jane Smith',
            email='jane.smith@example.com',
            username='janesmith',
            password='newpassword123'
        ))
        self.assertEqual(res.status_code, 200)
        self.assertIn('User updated successfully', res.get_json()['success'])


class TestProjects(TestBase):
    """Tests for the project endpoints."""

    def setUp(self):
        super().setUp()


class TestTasks(TestBase):
    """Tests for the tasks endpoints."""

    def setUp(self):
        super().setUp()
