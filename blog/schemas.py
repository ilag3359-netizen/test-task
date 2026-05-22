from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from ninja import Schema


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterIn(Schema):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def username_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Username не может быть пустым')
        if len(v) < 3:
            raise ValueError('Username должен содержать минимум 3 символа')
        return v

    @field_validator('password')
    @classmethod
    def password_not_empty(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v


class RegisterOut(Schema):
    id: int
    username: str
    token: str


class LoginIn(Schema):
    username: str
    password: str


class LoginOut(Schema):
    token: str
    username: str


class MessageOut(Schema):
    message: str


# ─── Category Schemas ─────────────────────────────────────────────────────────

class CategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str


# ─── Article Schemas ──────────────────────────────────────────────────────────

class ArticleIn(Schema):
    title: str
    content: str
    category_id: Optional[int] = None
    is_published: bool = True

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Заголовок не может быть пустым')
        return v

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Содержимое не может быть пустым')
        return v


class ArticleUpdateIn(Schema):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    is_published: Optional[bool] = None


class ArticleAuthorOut(Schema):
    id: int
    username: str


class ArticleOut(Schema):
    id: int
    title: str
    content: str
    author: ArticleAuthorOut
    category: Optional[CategoryOut] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_author(obj):
        return obj.author

    @staticmethod
    def resolve_category(obj):
        return obj.category


class ArticleListOut(Schema):
    id: int
    title: str
    author: ArticleAuthorOut
    category: Optional[CategoryOut] = None
    is_published: bool
    created_at: datetime

    @staticmethod
    def resolve_author(obj):
        return obj.author

    @staticmethod
    def resolve_category(obj):
        return obj.category


# ─── Comment Schemas ──────────────────────────────────────────────────────────

class CommentIn(Schema):
    content: str

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Текст комментария не может быть пустым')
        return v


class CommentUpdateIn(Schema):
    content: str

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Текст комментария не может быть пустым')
        return v


class CommentAuthorOut(Schema):
    id: int
    username: str


class CommentOut(Schema):
    id: int
    article_id: int
    author: CommentAuthorOut
    content: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_author(obj):
        return obj.author
