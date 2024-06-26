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
        self.assertEqual(res.status_code, 401)

    def test_user_register(self):
        """Tests user registration"""
        response = self.client.post('/api/user/register/', data=dict(
            name='John Doe',
            email='john@example.com',
            username='johndoe',
            password='password123'
        ))
        self.assertEqual(response.status_code, 201)
        self.assertIn('User registered successfully', response.get_json()['message'])

    def test_user_detail(self):
        """Tests user detail"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/user/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('homer', res.get_json()['user']['username'])

    def test_user_update(self):
        credentials = auth_header('homer', '1234')
        res = self.client.put('/api/user/', headers=credentials, data=dict(
            name='Jane Smith',
            email='jane.smith@example.com',
            username='janesmith',
            password='newpassword123'
        ))
        self.assertEqual(res.status_code, 200)
        self.assertIn('User updated successfully', res.get_json()['message'])


class TestProjects(TestBase):
    """Tests for the project endpoints."""

    def setUp(self):
        super().setUp()

    def test_get_projects(self):
        """Tests project list endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/projects/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json()['projects'], list)

    def test_add_project(self):
        """Tests add project endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.post('/api/projects/', headers=credentials, data=dict(
            title='project_test'
        ))
        self.assertEqual(res.status_code, 201)
        self.assertIn('Project added successfully', res.get_json()['message'])

    def test_get_project_with_id(self):
        """Tests project list endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/projects/1/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('id', res.get_json()['project'])

    def test_update_project(self):
        """Tests update project endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.put('/api/projects/1/', headers=credentials, data=dict(
            title='project_test_updated'
        ))
        self.assertEqual(res.status_code, 200)
        self.assertIn('Project updated successfully', res.get_json()['message'])

    def test_delete_project(self):
        """Tests delete project endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.delete('/api/projects/1/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Project deleted successfully', res.get_json()['message'])


class TestTasks(TestBase):
    """Tests for the tasks endpoints."""

    def setUp(self):
        super().setUp()

    def test_get_tasks(self):
        """Tests task list endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/projects/1/tasks/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('tasks', res.get_json())
        self.assertIsInstance(res.get_json()['tasks'], list)

    def test_add_task(self):
        """Tests add task endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.post('/api/projects/1/tasks/', headers=credentials, data=dict(
            title='task_test'
        ))
        self.assertEqual(res.status_code, 201)
        self.assertIn('Task added successfully', res.get_json()['message'])

    def test_get_task_with_id(self):
        """Tests task list endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/projects/1/tasks/1/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('id', res.get_json()['task'])

    def test_update_task(self):
        """Tests update task endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.put('/api/projects/1/tasks/1/', headers=credentials, data=dict(
            completed=0,
            title='task_test_updated'
        ))
        self.assertEqual(res.status_code, 200)
        self.assertIn('Task updated successfully', res.get_json()['message'])

    def test_delete_task(self):
        """Tests delete task endpoint"""
        credentials = auth_header('homer', '1234')
        res = self.client.delete('/api/projects/1/tasks/1/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Task deleted successfully', res.get_json()['message'])


class TestCollaborators(TestBase):
    def setUp(self):
        super().setUp()

    def test_get_collaborators(self):
        credentials = auth_header('homer', '1234')
        res = self.client.get('/api/projects/1/collaborators/', headers=credentials)
        self.assertEqual(res.status_code, 200)
        self.assertIn('collaborators', res.get_json())
        self.assertIsInstance(res.get_json()['collaborators'], list)

    def test_add_collaborator(self):
        credentials = auth_header('homer', '1234')
        res = self.client.post('/api/projects/1/collaborators/', headers=credentials, data={
            'user_id': '2'
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn('Collaborator added successfully', res.get_json()['message'])
        self.assertIn('collaborator', res.get_json())

    def test_remove_collaborator(self):
        credentials = auth_header('homer', '1234')
        self.client.post('/api/projects/1/collaborators/', headers=credentials, data={
            'user_id': '2'
        })
        res = self.client.delete('/api/projects/1/collaborators/', headers=credentials, data={
            'user_id': '2'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('Collaborator removed successfully', res.get_json()['message'])

