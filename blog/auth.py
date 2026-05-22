import logging
from typing import Optional
from django.http import HttpRequest
from django.contrib.auth.models import User
from ninja.security import HttpBearer
from ninja import Schema
from .models import UserToken

logger = logging.getLogger('blog')


class TokenAuth(HttpBearer):
    """Аутентификация по токену из заголовка Authorization: Bearer <token>."""

    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        try:
            user_token = UserToken.objects.select_related('user').get(token=token)
            return user_token.user
        except UserToken.DoesNotExist:
            logger.warning(f'Попытка авторизации с неверным токеном: {token[:20]}...')
            return None


class BodyTokenAuth:
    """
    Аутентификация по токену из тела запроса (поле token).
    Используется как fallback — пользователь может передать token в body.
    """
    openapi_type = 'apiKey'
    openapi_name = 'token'

    def __call__(self, request: HttpRequest) -> Optional[User]:
        token = request.POST.get('token') or (
            request.body and __import__('json').loads(request.body).get('token')
            if request.content_type == 'application/json'
            else None
        )
        if not token:
            return None
        try:
            user_token = UserToken.objects.select_related('user').get(token=token)
            return user_token.user
        except (UserToken.DoesNotExist, Exception):
            return None


token_auth = TokenAuth()
