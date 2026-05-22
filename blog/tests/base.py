from django.test import TestCase, Client
from django.contrib.auth.models import User
from blog.models import UserToken, Category, Article, Comment


class BlogTestCase(TestCase):
    """Базовый класс для тестов с вспомогательными методами."""

    def setUp(self):
        self.client = Client()
        self.user = self._create_user('testuser', 'testpass123')
        self.other_user = self._create_user('otheruser', 'otherpass123')
        self.token = UserToken.objects.get(user=self.user).token
        self.other_token = UserToken.objects.get(user=self.other_user).token
        self.category = Category.objects.create(
            name='Технологии', slug='tech', description='IT статьи'
        )

    def _create_user(self, username: str, password: str) -> User:
        user = User.objects.create_user(username=username, password=password)
        UserToken.objects.create(user=user)
        return user

    def _auth_headers(self, token: str = None) -> dict:
        return {'HTTP_AUTHORIZATION': f'Bearer {token or self.token}'}

    def _create_article(self, user=None, title='Тестовая статья', published=True) -> Article:
        return Article.objects.create(
            title=title,
            content='Содержимое тестовой статьи.',
            author=user or self.user,
            category=self.category,
            is_published=published,
        )

    def _create_comment(self, article, user=None, content='Тестовый комментарий') -> Comment:
        return Comment.objects.create(
            article=article,
            author=user or self.user,
            content=content,
        )
