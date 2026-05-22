import json
from blog.models import Article
from .base import BlogTestCase


class ListArticlesTestCase(BlogTestCase):
    """Тесты для GET /api/articles/"""

    def test_list_articles_empty(self):
        """Пустой список статей."""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_articles_with_data(self):
        """Список статей возвращает опубликованные статьи."""
        self._create_article(title='Статья 1')
        self._create_article(title='Статья 2')
        self._create_article(title='Неопубликованная', published=False)
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_list_articles_filter_by_category(self):
        """Фильтрация статей по категории."""
        self._create_article(title='Статья в категории')
        response = self.client.get(f'/api/articles/?category_id={self.category.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_articles_filter_wrong_category(self):
        """Фильтрация по несуществующей категории — пустой список."""
        self._create_article()
        response = self.client.get('/api/articles/?category_id=9999')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class GetArticleTestCase(BlogTestCase):
    """Тесты для GET /api/articles/{id}"""

    def test_get_article_success(self):
        """Успешное получение статьи по ID."""
        article = self._create_article(title='Моя статья')
        response = self.client.get(f'/api/articles/{article.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Моя статья')
        self.assertEqual(data['author']['username'], 'testuser')

    def test_get_article_not_found(self):
        """Статья не найдена — ошибка 404."""
        response = self.client.get('/api/articles/99999')
        self.assertEqual(response.status_code, 404)


class CreateArticleTestCase(BlogTestCase):
    """Тесты для POST /api/articles/"""

    def test_create_article_success(self):
        """Успешное создание статьи."""
        response = self.client.post(
            '/api/articles/',
            data=json.dumps({
                'title': 'Новая статья',
                'content': 'Содержимое статьи.',
                'category_id': self.category.id,
            }),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['title'], 'Новая статья')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertTrue(Article.objects.filter(title='Новая статья').exists())

    def test_create_article_without_auth(self):
        """Создание статьи без авторизации — ошибка 401."""
        response = self.client.post(
            '/api/articles/',
            data=json.dumps({'title': 'Статья', 'content': 'Контент'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_create_article_empty_title(self):
        """Создание статьи с пустым заголовком — ошибка 422."""
        response = self.client.post(
            '/api/articles/',
            data=json.dumps({'title': '', 'content': 'Контент'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 422)

    def test_create_article_wrong_category(self):
        """Создание статьи с несуществующей категорией — ошибка 400."""
        response = self.client.post(
            '/api/articles/',
            data=json.dumps({'title': 'Статья', 'content': 'Контент', 'category_id': 9999}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 400)


class UpdateArticleTestCase(BlogTestCase):
    """Тесты для PUT /api/articles/{id}"""

    def test_update_article_success(self):
        """Успешное обновление статьи автором."""
        article = self._create_article()
        response = self.client.put(
            f'/api/articles/{article.id}',
            data=json.dumps({'title': 'Обновлённый заголовок'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Обновлённый заголовок')

    def test_update_article_by_other_user(self):
        """Обновление чужой статьи — ошибка 403."""
        article = self._create_article()
        response = self.client.put(
            f'/api/articles/{article.id}',
            data=json.dumps({'title': 'Взлом'}),
            content_type='application/json',
            **self._auth_headers(self.other_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_update_article_not_found(self):
        """Обновление несуществующей статьи — ошибка 404."""
        response = self.client.put(
            '/api/articles/99999',
            data=json.dumps({'title': 'Что-то'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_update_article_without_auth(self):
        """Обновление статьи без авторизации — ошибка 401."""
        article = self._create_article()
        response = self.client.put(
            f'/api/articles/{article.id}',
            data=json.dumps({'title': 'Хак'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)


class DeleteArticleTestCase(BlogTestCase):
    """Тесты для DELETE /api/articles/{id}"""

    def test_delete_article_success(self):
        """Успешное удаление статьи автором."""
        article = self._create_article()
        article_id = article.id
        response = self.client.delete(
            f'/api/articles/{article_id}',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(id=article_id).exists())

    def test_delete_article_by_other_user(self):
        """Удаление чужой статьи — ошибка 403."""
        article = self._create_article()
        response = self.client.delete(
            f'/api/articles/{article.id}',
            **self._auth_headers(self.other_token),
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(id=article.id).exists())

    def test_delete_article_not_found(self):
        """Удаление несуществующей статьи — ошибка 404."""
        response = self.client.delete(
            '/api/articles/99999',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_article_without_auth(self):
        """Удаление статьи без авторизации — ошибка 401."""
        article = self._create_article()
        response = self.client.delete(f'/api/articles/{article.id}')
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Article.objects.filter(id=article.id).exists())
