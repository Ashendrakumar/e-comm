import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

STRONG = 'Correct-Horse-42'


class AuthApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def register(self, **extra):
        data = {'email': 'Asha@Example.com', 'password': STRONG, 'first_name': 'Asha', **extra}
        return self.client.post('/api/v1/auth/register/', data, format='json')

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_register_returns_token_and_user(self):
        resp = self.register()
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body['user']['email'], 'Asha@example.com')        # domain normalised
        self.assertTrue(Token.objects.filter(key=body['token']).exists())

    def test_register_rejects_duplicate_email_any_case_and_weak_password(self):
        self.register()
        self.assertIn('email', self.register(email='asha@EXAMPLE.com').json())
        self.assertIn('password', self.register(email='b@example.com', password='12345678').json())

    def test_login_with_email_or_username(self):
        self.register()
        user = User.objects.get()
        for login in ('asha@example.com', user.username):
            resp = self.client.post('/api/v1/auth/login/', {'login': login, 'password': STRONG}, format='json')
            self.assertEqual(resp.status_code, 200, login)
        bad = self.client.post('/api/v1/auth/login/', {'login': 'asha@example.com', 'password': 'nope'})
        self.assertEqual(bad.status_code, 400)

    def test_me_requires_token_and_updates_profile(self):
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 401)
        self.auth(self.register().json()['token'])
        resp = self.client.patch('/api/v1/auth/me/', {'last_name': 'Patel'}, format='json')
        self.assertEqual(resp.json()['last_name'], 'Patel')
        self.assertEqual(self.client.patch('/api/v1/auth/me/', {'email': ''}, format='json').status_code, 400)

    def test_logout_revokes_token(self):
        self.auth(self.register().json()['token'])
        self.assertEqual(self.client.post('/api/v1/auth/logout/').status_code, 204)
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 401)

    def test_change_password_rotates_token(self):
        old = self.register().json()['token']
        self.auth(old)
        wrong = self.client.post('/api/v1/auth/change-password/',
                                 {'old_password': 'x', 'new_password': 'Another-Pass-77'}, format='json')
        self.assertEqual(wrong.status_code, 400)
        resp = self.client.post('/api/v1/auth/change-password/',
                                {'old_password': STRONG, 'new_password': 'Another-Pass-77'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.json()['token'], old)
        self.assertFalse(Token.objects.filter(key=old).exists())

    def test_password_reset_flow(self):
        self.register()
        resp = self.client.post('/api/v1/auth/password-reset/', {'email': 'asha@example.com'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        body  = mail.outbox[0].body
        uid   = re.search(r'Reset ID: (\S+)', body)[1]
        token = re.search(r'Reset code: (\S+)', body)[1]

        bad = self.client.post('/api/v1/auth/password-reset/confirm/',
                               {'uid': uid, 'token': 'wrong', 'new_password': 'Brand-New-99'}, format='json')
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post('/api/v1/auth/password-reset/confirm/',
                              {'uid': uid, 'token': token, 'new_password': 'Brand-New-99'}, format='json')
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(User.objects.get().check_password('Brand-New-99'))
        reused = self.client.post('/api/v1/auth/password-reset/confirm/',
                                  {'uid': uid, 'token': token, 'new_password': 'Brand-New-100'}, format='json')
        self.assertEqual(reused.status_code, 400)                           # a code works once

    @override_settings(API_PASSWORD_RESET_URL='techzone://reset?uid={uid}&token={token}')
    def test_password_reset_email_includes_deep_link(self):
        self.register()
        self.client.post('/api/v1/auth/password-reset/', {'email': 'asha@example.com'}, format='json')
        self.assertIn('techzone://reset?uid=', mail.outbox[0].body)

    def test_password_reset_does_not_reveal_unknown_emails(self):
        resp = self.client.post('/api/v1/auth/password-reset/', {'email': 'ghost@example.com'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_delete_account_needs_password_and_refuses_staff(self):
        self.auth(self.register().json()['token'])
        self.assertEqual(self.client.post('/api/v1/auth/delete-account/', {'password': 'x'}).status_code, 400)
        self.assertEqual(self.client.post('/api/v1/auth/delete-account/', {'password': STRONG}).status_code, 204)
        self.assertFalse(User.objects.exists())

        staff = User.objects.create_user('boss', 'boss@example.com', STRONG, is_staff=True)
        self.auth(Token.objects.create(user=staff).key)
        self.assertEqual(self.client.post('/api/v1/auth/delete-account/', {'password': STRONG}).status_code, 403)

    @override_settings(RATELIMIT_ENABLED=True, RATELIMIT_LOGIN='2/15m')
    def test_login_is_rate_limited(self):
        for _ in range(2):
            self.client.post('/api/v1/auth/login/', {'login': 'a@b.com', 'password': 'x'})
        self.assertEqual(self.client.post('/api/v1/auth/login/', {'login': 'a@b.com', 'password': 'x'}).status_code,
                         429)
