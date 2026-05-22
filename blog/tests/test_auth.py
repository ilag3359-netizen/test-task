import json
from django.contrib.auth.models import User
from blog.models import UserToken
from .base import BlogTestCase


class RegisterTestCase(BlogTestCase):
    """Тесты для POST /api/auth/register"""

    def test_register_success(self):
        """Успешная регистрация нового пользователя."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'newuser', 'password': 'newpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('token', data)
        self.assertEqual(data['username'], 'newuser')
        self.assertEqual(len(data['token']), 256)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Регистрация с уже существующим username — ошибка 400."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'testuser', 'password': 'pass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('уже существует', response.json()['message'])

    def test_register_empty_username(self):
        """Регистрация с пустым username — ошибка 422."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': '', 'password': 'pass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 422)

    def test_register_short_password(self):
        """Регистрация со слишком коротким паролем — ошибка 422."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'newuser2', 'password': '123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 422)

    def test_register_token_is_256_chars(self):
        """Токен после регистрации должен быть ровно 256 символов."""
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'tokenuser', 'password': 'tokenpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()['token']), 256)


class LoginTestCase(BlogTestCase):
    """Тесты для POST /api/auth/login"""

    def test_login_success(self):
        """Успешный вход."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'testuser', 'password': 'testpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('token', data)
        self.assertEqual(data['username'], 'testuser')

    def test_login_wrong_password(self):
        """Вход с неверным паролем — ошибка 401."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'testuser', 'password': 'wrongpass'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """Вход несуществующего пользователя — ошибка 401."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'nobody', 'password': 'pass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_login_returns_correct_token(self):
        """Токен при входе совпадает с токеном в БД."""
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'testuser', 'password': 'testpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        db_token = UserToken.objects.get(user=self.user).token
        self.assertEqual(response.json()['token'], db_token)


class LogoutTestCase(BlogTestCase):
    """Тесты для POST /api/auth/logout"""

    def test_logout_success(self):
        """Успешный выход — токен инвалидируется."""
        old_token = self.token
        response = self.client.post(
            '/api/auth/logout',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        # Старый токен больше не должен работать
        new_token = UserToken.objects.get(user=self.user).token
        self.assertNotEqual(old_token, new_token)

    def test_logout_without_token(self):
        """Выход без токена — ошибка 401."""
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, 401)

    def test_logout_with_invalid_token(self):
        """Выход с неверным токеном — ошибка 401."""
        response = self.client.post(
            '/api/auth/logout',
            HTTP_AUTHORIZATION='Bearer invalidtoken123',
        )
        self.assertEqual(response.status_code, 401)
