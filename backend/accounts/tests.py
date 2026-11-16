from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status

User = get_user_model()


class AuthSessionLifecycleTests(TestCase):
    def setUp(self):
        self.username = 'qa-browser-user'
        self.password = 'StrongPass123!'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_creates_session_cookie(self):
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': self.username, 'password': self.password},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sessionid', self.client.cookies)
        self.assertEqual(response.json()['user']['username'], self.username)

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': self.username, 'password': 'wrong-password'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_current_user_endpoint_works(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], self.username)

    def test_logout_invalidates_session(self):
        self.client.login(username=self.username, password=self.password)
        logout_response = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        follow_up = self.client.get('/api/v1/auth/me/')
        self.assertEqual(follow_up.status_code, status.HTTP_403_FORBIDDEN)

    def test_protected_business_listing_requires_auth(self):
        response = self.client.get('/api/v1/businesses/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
