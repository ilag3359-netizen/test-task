# 📝 Blog API

Бэкенд для блога на Django + Django Ninja с авторизацией по токену, CRUD для статей и комментариев, админ-панелью и полным покрытием тестами.

## 🚀 Технологии

- **Python 3.10+**
- **Django 4.2** + **Django Ninja** (REST API)
- **Django Ninja JWT** (JWT авторизация)
- **PostgreSQL** (база данных)
- **Docker / docker-compose**
- **pytest + pytest-django** (тестирование)
- **structlog / logging** (логирование)
- **GitHub Actions** (CI/CD)

---

## ⚙️ Быстрый старт

### Вариант 1 — Docker (рекомендуется)

```bash
git clone https://github.com/YOUR_USERNAME/blog-api.git
cd blog-api

cp .env.example .env   # при необходимости отредактируй

docker-compose up --build
```

После запуска:
- **Swagger UI:** http://localhost:8000/api/docs
- **Админ-панель:** http://localhost:8000/admin/

Создать суперпользователя:
```bash
docker-compose exec web python manage.py createsuperuser
```

---

### Вариант 2 — Локально (без Docker)

**1. Клонировать репозиторий**
```bash
git clone https://github.com/YOUR_USERNAME/blog-api.git
cd blog-api
```

**2. Создать и активировать виртуальное окружение**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Установить зависимости**
```bash
pip install -r requirements.txt
```

**4. Создать базу данных PostgreSQL**
```sql
CREATE DATABASE blog_db;
CREATE USER blog_user WITH PASSWORD 'blog_password';
GRANT ALL PRIVILEGES ON DATABASE blog_db TO blog_user;
GRANT ALL ON SCHEMA public TO blog_user;
ALTER DATABASE blog_db OWNER TO blog_user;
```

**5. Настроить `.env`**
```bash
cp .env.example .env
```
Открыть `.env` и убедиться что `POSTGRES_HOST=localhost`.

**6. Применить миграции и запустить**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🔑 Авторизация

Проект поддерживает два способа авторизации:

### Token (основной — 256 символов)
1. Зарегистрироваться: `POST /api/auth/register`
2. Получить токен в ответе
3. Передавать в заголовке: `Authorization: Bearer <token>`

### JWT (дополнительно)
- Получить пару токенов: `POST /api/jwt/pair`
- Обновить: `POST /api/jwt/refresh`

---

## 📡 Эндпоинты API

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register` | Регистрация, возвращает токен 256 символов |
| POST | `/api/auth/login` | Вход, возвращает токен |
| POST | `/api/auth/logout` | Выход, инвалидирует токен |

### Articles
| Метод | URL | Auth | Описание |
|-------|-----|------|----------|
| GET | `/api/articles/` | — | Список опубликованных статей |
| GET | `/api/articles/{id}` | — | Получить статью |
| POST | `/api/articles/` | ✅ | Создать статью |
| PUT | `/api/articles/{id}` | ✅ | Обновить свою статью |
| DELETE | `/api/articles/{id}` | ✅ | Удалить свою статью |

### Comments
| Метод | URL | Auth | Описание |
|-------|-----|------|----------|
| GET | `/api/articles/{id}/comments` | — | Список комментариев |
| POST | `/api/articles/{id}/comments` | ✅ | Создать комментарий |
| PUT | `/api/articles/comments/{id}` | ✅ | Обновить свой комментарий |
| DELETE | `/api/articles/comments/{id}` | ✅ | Удалить свой комментарий |

### Categories
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/categories/` | Список категорий |
| GET | `/api/categories/{id}` | Получить категорию |

---

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest

# С подробным выводом
pytest -v

# Внутри Docker
docker-compose exec web pytest
```

**Покрытие:** 51 тест по всем эндпоинтам (auth, articles, comments, categories).  
Каждый эндпоинт покрыт минимум 2 тестами — успешный и неуспешный сценарий.

---

## 📋 Логирование

Логи пишутся в папку `logs/`:
- `logs/info.log` — все INFO+ события
- `logs/error.log` — только ERROR события
- Консоль — все события в реальном времени

Логируются:
- Регистрация / вход / выход пользователей
- CRUD операции со статьями и комментариями
- Ошибки авторизации и доступа

---

## 🏗️ Структура проекта

```
blog_project/
├── .env.example
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── pytest.ini
├── requirements.txt
├── config/
│   ├── settings.py            # Настройки Django
│   ├── urls.py
│   └── wsgi.py
└── blog/
    ├── models.py              # UserToken, Category, Article, Comment
    ├── schemas.py             # Pydantic-схемы
    ├── api.py                 # Все эндпоинты
    ├── auth.py                # Bearer Token аутентификация
    ├── admin.py               # Админ-панель
    ├── migrations/
    └── tests/
        ├── base.py
        ├── test_auth.py
        ├── test_articles.py
        ├── test_comments.py
        └── test_categories.py
```

---

## 🔧 Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Режим отладки | `True` |
| `ALLOWED_HOSTS` | Разрешённые хосты | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Имя БД | `blog_db` |
| `POSTGRES_USER` | Пользователь БД | `blog_user` |
| `POSTGRES_PASSWORD` | Пароль БД | `blog_password` |
| `POSTGRES_HOST` | Хост БД | `db` (Docker) / `localhost` |
| `POSTGRES_PORT` | Порт БД | `5432` |

---

## 🚢 CI/CD

GitHub Actions автоматически:
1. **При каждом push** — запускает все 51 тест
2. **При merge в main** — собирает Docker-образ и пушит на Docker Hub
3. **После сборки** — деплоит на VPS через SSH

Для активации деплоя добавь в GitHub Secrets:
- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`
