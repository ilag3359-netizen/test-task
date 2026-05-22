from blog.models import Category
from .base import BlogTestCase


class ListCategoriesTestCase(BlogTestCase):
    """Тесты для GET /api/categories/"""

    def test_list_categories_success(self):
        """Список категорий возвращает существующие категории."""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # В setUp создаётся одна категория
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Технологии')
        self.assertEqual(data[0]['slug'], 'tech')

    def test_list_categories_no_auth_required(self):
        """Просмотр категорий не требует авторизации."""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)

    def test_list_categories_multiple(self):
        """Несколько категорий возвращаются все."""
        Category.objects.create(name='Наука', slug='science', description='Научные статьи')
        Category.objects.create(name='Спорт', slug='sport', description='Спортивные статьи')
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)  # 1 из setUp + 2 новых


class GetCategoryTestCase(BlogTestCase):
    """Тесты для GET /api/categories/{id}"""

    def test_get_category_success(self):
        """Успешное получение категории по ID."""
        response = self.client.get(f'/api/categories/{self.category.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Технологии')
        self.assertEqual(data['slug'], 'tech')

    def test_get_category_not_found(self):
        """Несуществующая категория — ошибка 404."""
        response = self.client.get('/api/categories/99999')
        self.assertEqual(response.status_code, 404)
