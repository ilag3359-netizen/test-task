import json
from blog.models import Comment
from .base import BlogTestCase


class ListCommentsTestCase(BlogTestCase):
    """Тесты для GET /api/articles/{article_id}/comments"""

    def test_list_comments_empty(self):
        """Пустой список комментариев."""
        article = self._create_article()
        response = self.client.get(f'/api/articles/{article.id}/comments')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_comments_with_data(self):
        """Список комментариев к статье."""
        article = self._create_article()
        self._create_comment(article, content='Первый комментарий')
        self._create_comment(article, user=self.other_user, content='Второй комментарий')
        response = self.client.get(f'/api/articles/{article.id}/comments')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_list_comments_article_not_found(self):
        """Статья не найдена — ошибка 404."""
        response = self.client.get('/api/articles/99999/comments')
        self.assertEqual(response.status_code, 404)

    def test_list_comments_no_auth_required(self):
        """Просмотр комментариев не требует авторизации."""
        article = self._create_article()
        self._create_comment(article)
        response = self.client.get(f'/api/articles/{article.id}/comments')
        self.assertEqual(response.status_code, 200)


class CreateCommentTestCase(BlogTestCase):
    """Тесты для POST /api/articles/{article_id}/comments"""

    def test_create_comment_success(self):
        """Успешное создание комментария."""
        article = self._create_article()
        response = self.client.post(
            f'/api/articles/{article.id}/comments',
            data=json.dumps({'content': 'Мой комментарий'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['content'], 'Мой комментарий')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertTrue(Comment.objects.filter(content='Мой комментарий').exists())

    def test_create_comment_without_auth(self):
        """Создание комментария без авторизации — ошибка 401."""
        article = self._create_article()
        response = self.client.post(
            f'/api/articles/{article.id}/comments',
            data=json.dumps({'content': 'Анонимный комментарий'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_create_comment_article_not_found(self):
        """Комментарий к несуществующей статье — ошибка 404."""
        response = self.client.post(
            '/api/articles/99999/comments',
            data=json.dumps({'content': 'Комментарий'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_create_comment_empty_content(self):
        """Пустой текст комментария — ошибка 422."""
        article = self._create_article()
        response = self.client.post(
            f'/api/articles/{article.id}/comments',
            data=json.dumps({'content': ''}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 422)


class UpdateCommentTestCase(BlogTestCase):
    """Тесты для PUT /api/articles/comments/{comment_id}"""

    def test_update_comment_success(self):
        """Успешное обновление комментария автором."""
        article = self._create_article()
        comment = self._create_comment(article)
        response = self.client.put(
            f'/api/articles/comments/{comment.id}',
            data=json.dumps({'content': 'Обновлённый комментарий'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['content'], 'Обновлённый комментарий')

    def test_update_comment_by_other_user(self):
        """Обновление чужого комментария — ошибка 403."""
        article = self._create_article()
        comment = self._create_comment(article)
        response = self.client.put(
            f'/api/articles/comments/{comment.id}',
            data=json.dumps({'content': 'Взлом'}),
            content_type='application/json',
            **self._auth_headers(self.other_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_update_comment_not_found(self):
        """Обновление несуществующего комментария — ошибка 404."""
        response = self.client.put(
            '/api/articles/comments/99999',
            data=json.dumps({'content': 'Что-то'}),
            content_type='application/json',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_update_comment_without_auth(self):
        """Обновление без авторизации — ошибка 401."""
        article = self._create_article()
        comment = self._create_comment(article)
        response = self.client.put(
            f'/api/articles/comments/{comment.id}',
            data=json.dumps({'content': 'Хак'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)


class DeleteCommentTestCase(BlogTestCase):
    """Тесты для DELETE /api/articles/comments/{comment_id}"""

    def test_delete_comment_success(self):
        """Успешное удаление комментария автором."""
        article = self._create_article()
        comment = self._create_comment(article)
        comment_id = comment.id
        response = self.client.delete(
            f'/api/articles/comments/{comment_id}',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_delete_comment_by_other_user(self):
        """Удаление чужого комментария — ошибка 403."""
        article = self._create_article()
        comment = self._create_comment(article)
        response = self.client.delete(
            f'/api/articles/comments/{comment.id}',
            **self._auth_headers(self.other_token),
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_delete_comment_not_found(self):
        """Удаление несуществующего комментария — ошибка 404."""
        response = self.client.delete(
            '/api/articles/comments/99999',
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_comment_without_auth(self):
        """Удаление комментария без авторизации — ошибка 401."""
        article = self._create_article()
        comment = self._create_comment(article)
        response = self.client.delete(f'/api/articles/comments/{comment.id}')
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())
