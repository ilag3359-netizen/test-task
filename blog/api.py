import logging
from typing import List, Optional
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from ninja_jwt.routers.obtain import obtain_pair_router

from .models import UserToken, Article, Comment, Category
from .schemas import (
    RegisterIn, RegisterOut, LoginIn, LoginOut, MessageOut,
    ArticleIn, ArticleUpdateIn, ArticleOut, ArticleListOut,
    CommentIn, CommentUpdateIn, CommentOut,
    CategoryOut,
)
from .auth import token_auth

logger = logging.getLogger('blog')

# ─── API instance ─────────────────────────────────────────────────────────────
api = NinjaAPI(
    title='Blog API',
    description='Бэкенд для блога с авторизацией, статьями, комментариями и категориями.',
    version='1.0.0',
)

# Подключаем JWT роутер (доп. плюс из ТЗ)
api.add_router('/jwt/', obtain_pair_router)


# ─── Auth Router ──────────────────────────────────────────────────────────────
auth_router = Router(tags=['Auth'])


@auth_router.post('/register', response={201: RegisterOut, 400: MessageOut})
def register(request: HttpRequest, payload: RegisterIn):
    """Регистрация пользователя. Сервер генерирует токен из 256 символов."""
    if User.objects.filter(username=payload.username).exists():
        logger.warning(f'Попытка регистрации с существующим username: {payload.username}')
        return 400, {'message': f'Пользователь с username "{payload.username}" уже существует'}

    user = User.objects.create_user(
        username=payload.username,
        password=payload.password,
    )
    user_token = UserToken.objects.create(user=user)

    logger.info(f'Зарегистрирован новый пользователь: {user.username} (id={user.id})')
    return 201, {
        'id': user.id,
        'username': user.username,
        'token': user_token.token,
    }


@auth_router.post('/login', response={200: LoginOut, 401: MessageOut})
def login(request: HttpRequest, payload: LoginIn):
    """Авторизация пользователя. Возвращает токен."""
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        logger.warning(f'Неудачная попытка входа для username: {payload.username}')
        return 401, {'message': 'Неверный username или пароль'}

    token_obj, _ = UserToken.objects.get_or_create(user=user)

    logger.info(f'Пользователь вошёл в систему: {user.username} (id={user.id})')
    return 200, {'token': token_obj.token, 'username': user.username}


@auth_router.post('/logout', auth=token_auth, response={200: MessageOut})
def logout(request: HttpRequest):
    """Выход из системы (инвалидирует текущий токен, генерирует новый)."""
    user = request.auth
    try:
        token_obj = UserToken.objects.get(user=user)
        # Генерируем новый токен — старый становится невалидным
        from .models import generate_token
        token_obj.token = generate_token()
        token_obj.save()
        logger.info(f'Пользователь вышел из системы: {user.username} (id={user.id})')
    except UserToken.DoesNotExist:
        logger.error(f'Токен не найден для пользователя: {user.username}')

    return 200, {'message': 'Вы успешно вышли из системы'}


api.add_router('/auth/', auth_router)


# ─── Articles Router ──────────────────────────────────────────────────────────
articles_router = Router(tags=['Articles'])


@articles_router.get('', response=List[ArticleListOut])
def list_articles(request: HttpRequest, category_id: Optional[int] = None):
    """Список всех опубликованных статей."""
    qs = Article.objects.select_related('author', 'category').filter(is_published=True)
    if category_id:
        qs = qs.filter(category_id=category_id)
    logger.info(f'Запрос списка статей (category_id={category_id}), найдено: {qs.count()}')
    return list(qs)


@articles_router.get('/{article_id}', response={200: ArticleOut, 404: MessageOut})
def get_article(request: HttpRequest, article_id: int):
    """Получить статью по ID."""
    try:
        article = Article.objects.select_related('author', 'category').get(id=article_id)
        logger.info(f'Просмотр статьи id={article_id}: "{article.title}"')
        return 200, article
    except Article.DoesNotExist:
        logger.warning(f'Статья не найдена: id={article_id}')
        return 404, {'message': f'Статья с id={article_id} не найдена'}


@articles_router.post('', auth=token_auth, response={201: ArticleOut, 400: MessageOut})
def create_article(request: HttpRequest, payload: ArticleIn):
    """Создать новую статью (требует авторизации)."""
    user = request.auth

    category = None
    if payload.category_id:
        try:
            category = Category.objects.get(id=payload.category_id)
        except Category.DoesNotExist:
            return 400, {'message': f'Категория с id={payload.category_id} не найдена'}

    article = Article.objects.create(
        title=payload.title,
        content=payload.content,
        author=user,
        category=category,
        is_published=payload.is_published,
    )
    logger.info(
        f'Создана статья id={article.id}: "{article.title}" '
        f'автором {user.username} (id={user.id})'
    )
    return 201, Article.objects.select_related('author', 'category').get(id=article.id)


@articles_router.put('/{article_id}', auth=token_auth, response={200: ArticleOut, 403: MessageOut, 404: MessageOut})
def update_article(request: HttpRequest, article_id: int, payload: ArticleUpdateIn):
    """Обновить статью (только автор)."""
    user = request.auth
    try:
        article = Article.objects.select_related('author', 'category').get(id=article_id)
    except Article.DoesNotExist:
        logger.warning(f'Попытка обновить несуществующую статью id={article_id}')
        return 404, {'message': f'Статья с id={article_id} не найдена'}

    if article.author != user:
        logger.warning(
            f'Пользователь {user.username} пытается обновить чужую статью id={article_id}'
        )
        return 403, {'message': 'Нет прав для редактирования этой статьи'}

    if payload.title is not None:
        article.title = payload.title
    if payload.content is not None:
        article.content = payload.content
    if payload.is_published is not None:
        article.is_published = payload.is_published
    if payload.category_id is not None:
        try:
            article.category = Category.objects.get(id=payload.category_id)
        except Category.DoesNotExist:
            return 400, {'message': f'Категория с id={payload.category_id} не найдена'}

    article.save()
    logger.info(
        f'Обновлена статья id={article_id}: "{article.title}" '
        f'пользователем {user.username} (id={user.id})'
    )
    return 200, Article.objects.select_related('author', 'category').get(id=article.id)


@articles_router.delete('/{article_id}', auth=token_auth, response={200: MessageOut, 403: MessageOut, 404: MessageOut})
def delete_article(request: HttpRequest, article_id: int):
    """Удалить статью (только автор)."""
    user = request.auth
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        logger.warning(f'Попытка удалить несуществующую статью id={article_id}')
        return 404, {'message': f'Статья с id={article_id} не найдена'}

    if article.author != user:
        logger.warning(
            f'Пользователь {user.username} пытается удалить чужую статью id={article_id}'
        )
        return 403, {'message': 'Нет прав для удаления этой статьи'}

    title = article.title
    article.delete()
    logger.info(
        f'Удалена статья id={article_id}: "{title}" '
        f'пользователем {user.username} (id={user.id})'
    )
    return 200, {'message': f'Статья "{title}" успешно удалена'}


api.add_router('/articles/', articles_router)


# ─── Comments Router ──────────────────────────────────────────────────────────
comments_router = Router(tags=['Comments'])


@comments_router.get('/{article_id}/comments', response={200: List[CommentOut], 404: MessageOut})
def list_comments(request: HttpRequest, article_id: int):
    """Список комментариев к статье."""
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return 404, {'message': f'Статья с id={article_id} не найдена'}

    comments = Comment.objects.select_related('author').filter(article=article)
    logger.info(f'Запрос комментариев к статье id={article_id}, найдено: {comments.count()}')
    return 200, list(comments)


@comments_router.post('/{article_id}/comments', auth=token_auth, response={201: CommentOut, 404: MessageOut})
def create_comment(request: HttpRequest, article_id: int, payload: CommentIn):
    """Создать комментарий к статье (требует авторизации)."""
    user = request.auth
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return 404, {'message': f'Статья с id={article_id} не найдена'}

    comment = Comment.objects.create(
        article=article,
        author=user,
        content=payload.content,
    )
    logger.info(
        f'Создан комментарий id={comment.id} к статье id={article_id} '
        f'пользователем {user.username} (id={user.id})'
    )
    return 201, Comment.objects.select_related('author').get(id=comment.id)


@comments_router.put('/comments/{comment_id}', auth=token_auth, response={200: CommentOut, 403: MessageOut, 404: MessageOut})
def update_comment(request: HttpRequest, comment_id: int, payload: CommentUpdateIn):
    """Обновить комментарий (только автор)."""
    user = request.auth
    try:
        comment = Comment.objects.select_related('author').get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f'Попытка обновить несуществующий комментарий id={comment_id}')
        return 404, {'message': f'Комментарий с id={comment_id} не найден'}

    if comment.author != user:
        logger.warning(
            f'Пользователь {user.username} пытается обновить чужой комментарий id={comment_id}'
        )
        return 403, {'message': 'Нет прав для редактирования этого комментария'}

    comment.content = payload.content
    comment.save()
    logger.info(
        f'Обновлён комментарий id={comment_id} '
        f'пользователем {user.username} (id={user.id})'
    )
    return 200, Comment.objects.select_related('author').get(id=comment.id)


@comments_router.delete('/comments/{comment_id}', auth=token_auth, response={200: MessageOut, 403: MessageOut, 404: MessageOut})
def delete_comment(request: HttpRequest, comment_id: int):
    """Удалить комментарий (только автор)."""
    user = request.auth
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f'Попытка удалить несуществующий комментарий id={comment_id}')
        return 404, {'message': f'Комментарий с id={comment_id} не найден'}

    if comment.author != user:
        logger.warning(
            f'Пользователь {user.username} пытается удалить чужой комментарий id={comment_id}'
        )
        return 403, {'message': 'Нет прав для удаления этого комментария'}

    comment.delete()
    logger.info(
        f'Удалён комментарий id={comment_id} '
        f'пользователем {user.username} (id={user.id})'
    )
    return 200, {'message': 'Комментарий успешно удалён'}


api.add_router('/articles/', comments_router)


# ─── Categories Router ────────────────────────────────────────────────────────
categories_router = Router(tags=['Categories'])


@categories_router.get('', response=List[CategoryOut])
def list_categories(request: HttpRequest):
    """Список всех категорий."""
    return list(Category.objects.all())


@categories_router.get('/{category_id}', response={200: CategoryOut, 404: MessageOut})
def get_category(request: HttpRequest, category_id: int):
    """Получить категорию по ID."""
    try:
        return 200, Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return 404, {'message': f'Категория с id={category_id} не найдена'}


api.add_router('/categories/', categories_router)
