# Архитектура DocuCraft

## Обзор

DocuCraft — модульный монолит, спроектированный с возможностью эволюции в микросервисную архитектуру.

## Структура проекта

```
docs_ai/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Точка входа FastAPI
│   │
│   ├── api/                    # API слой (HTTP endpoints)
│   │   ├── __init__.py
│   │   ├── deps.py             # FastAPI dependencies
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Аутентификация
│   │   │   ├── projects.py     # Проекты
│   │   │   ├── documents.py    # Документация
│   │   │   ├── git.py          # Git интеграция
│   │   │   └── ai.py           # AI предложения
│   │   └── websocket.py        # WebSocket для realtime
│   │
│   ├── domain/                 # Доменный слой (бизнес-логика)
│   │   ├── __init__.py
│   │   ├── models/             # Доменные модели (Pydantic)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── git_event.py
│   │   │   └── ai_suggestion.py
│   │   ├── services/           # Доменные сервисы
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── project_service.py
│   │   │   ├── document_service.py
│   │   │   ├── git_service.py
│   │   │   └── ai_service.py
│   │   └── repositories/       # Абстракции репозиториев
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── user_repository.py
│   │       ├── project_repository.py
│   │       └── document_repository.py
│   │
│   ├── infrastructure/         # Инфраструктурный слой
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Базовые классы SQLAlchemy
│   │   │   ├── models/         # SQLAlchemy ORM модели
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── project.py
│   │   │   │   ├── document.py
│   │   │   │   └── ...
│   │   │   ├── session.py      # Database session management
│   │   │   └── repositories/   # Реализации репозиториев
│   │   │       ├── __init__.py
│   │   │       ├── user_repository_impl.py
│   │   │       ├── project_repository_impl.py
│   │   │       └── document_repository_impl.py
│   │   ├── external/
│   │   │   ├── __init__.py
│   │   │   ├── github/         # GitHub API клиент
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py
│   │   │   │   └── webhook.py
│   │   │   └── ai/             # AI провайдеры
│   │   │       ├── __init__.py
│   │   │       ├── base.py     # Абстрактный интерфейс
│   │   │       ├── openai.py   # OpenAI реализация
│   │   │       └── anthropic.py # Anthropic реализация
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       └── file_storage.py # Хранение файлов (S3/local)
│   │
│   ├── core/                   # Ядро приложения
│   │   ├── __init__.py
│   │   ├── config.py           # Конфигурация
│   │   ├── security.py         # JWT, хеширование
│   │   └── exceptions.py       # Кастомные исключения
│   │
│   └── tasks/                  # Celery задачи
│       ├── __init__.py
│       ├── git_analysis.py     # Анализ git diff
│       └── ai_processing.py    # AI обработка
│
├── alembic/                    # Миграции БД
│   ├── versions/
│   └── env.py
│
├── tests/                      # Тесты
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                    # Вспомогательные скрипты
│
├── .env.example
├── .gitignore
├── pyproject.toml              # Зависимости и настройки
├── README.md
└── ARCHITECTURE.md             # Этот файл

```

## Принципы архитектуры

### 1. Слоистая архитектура

- **API Layer**: HTTP endpoints, валидация запросов, форматирование ответов
- **Domain Layer**: Бизнес-логика, доменные модели, сервисы
- **Infrastructure Layer**: БД, внешние API, кеш, файловое хранилище

### 2. Dependency Injection

Используем FastAPI dependencies для инверсии зависимостей:
- Репозитории внедряются в сервисы
- Сервисы внедряются в API endpoints
- Легко тестировать и мокать

### 3. Repository Pattern

Абстракция доступа к данным:
- Доменный слой работает с интерфейсами
- Инфраструктурный слой предоставляет реализации
- Легко заменить БД или добавить кеширование

### 4. Service Layer

Бизнес-логика изолирована в сервисах:
- Валидация
- Транзакции
- Координация между репозиториями

## Доменные сущности

### User (Пользователь)
- id, email, username
- hashed_password
- created_at, updated_at
- is_active, is_superuser

### Project (Проект)
- id, name, description
- owner_id (User)
- github_repo_url
- github_webhook_secret
- ai_mode (suggest-only / auto-apply)
- created_at, updated_at

### ProjectMember (Участник проекта)
- id, project_id, user_id
- role (Viewer, Editor, ProjectLead, Admin)
- created_at

### Document (Документ)
- id, project_id
- title, slug
- content (Markdown)
- content_json (структурированное представление для редактора)
- version
- git_commit_hash (привязка к коммиту)
- created_by_id, updated_by_id
- created_at, updated_at

### DocumentVersion (Версия документа)
- id, document_id
- version_number
- content, content_json
- git_commit_hash
- changed_by_id
- change_summary
- created_at

### GitEvent (Git событие)
- id, project_id
- event_type (push, merge, etc.)
- commit_hash, branch
- payload (JSON)
- processed (bool)
- created_at

### AISuggestion (AI предложение)
- id, document_id, git_event_id
- suggestion_type (update, add, delete)
- target_section (опционально)
- suggested_content
- status (pending, approved, rejected, applied)
- reviewed_by_id, reviewed_at
- created_at

### OpenAPISpec (OpenAPI спецификация)
- id, project_id
- spec_content (JSON)
- version
- git_commit_hash
- created_at, updated_at

## Схема базы данных

### Таблицы и связи

```
users
├── id (PK, UUID)
├── email (UNIQUE)
├── username
├── hashed_password
├── is_active
├── is_superuser
└── timestamps

projects
├── id (PK, UUID)
├── name
├── description
├── owner_id (FK -> users.id)
├── github_repo_url
├── github_webhook_secret
├── ai_mode (ENUM: suggest-only, auto-apply)
└── timestamps

project_members
├── id (PK, UUID)
├── project_id (FK -> projects.id)
├── user_id (FK -> users.id)
├── role (ENUM: Viewer, Editor, ProjectLead, Admin)
└── timestamps
UNIQUE(project_id, user_id)

documents
├── id (PK, UUID)
├── project_id (FK -> projects.id)
├── title
├── slug
├── content (TEXT - Markdown)
├── content_json (JSONB - структурированное представление)
├── version (INTEGER)
├── git_commit_hash
├── created_by_id (FK -> users.id)
├── updated_by_id (FK -> users.id)
└── timestamps
UNIQUE(project_id, slug)

document_versions
├── id (PK, UUID)
├── document_id (FK -> documents.id)
├── version_number (INTEGER)
├── content (TEXT)
├── content_json (JSONB)
├── git_commit_hash
├── changed_by_id (FK -> users.id)
├── change_summary
└── created_at

git_events
├── id (PK, UUID)
├── project_id (FK -> projects.id)
├── event_type (VARCHAR)
├── commit_hash
├── branch
├── payload (JSONB)
├── processed (BOOLEAN)
└── created_at

ai_suggestions
├── id (PK, UUID)
├── document_id (FK -> documents.id)
├── git_event_id (FK -> git_events.id)
├── suggestion_type (ENUM: update, add, delete)
├── target_section (VARCHAR, nullable)
├── suggested_content (TEXT)
├── status (ENUM: pending, approved, rejected, applied)
├── reviewed_by_id (FK -> users.id, nullable)
├── reviewed_at (TIMESTAMP, nullable)
└── created_at

openapi_specs
├── id (PK, UUID)
├── project_id (FK -> projects.id)
├── spec_content (JSONB)
├── version
├── git_commit_hash
└── timestamps
```

## Технологический стек

### Backend
- **FastAPI**: Асинхронный веб-фреймворк
- **SQLAlchemy 2.0**: ORM с async поддержкой
- **Alembic**: Миграции БД
- **PostgreSQL**: Основная БД
- **Redis**: Кеширование и Celery broker
- **Celery**: Асинхронные задачи
- **Pydantic**: Валидация и сериализация
- **PyJWT**: JWT токены
- **python-multipart**: Загрузка файлов

### External Services
- **GitHub API**: OAuth и webhooks
- **AI Providers**: OpenAI, Anthropic (абстракция)

## Безопасность

1. **Аутентификация**: JWT токены
2. **Авторизация**: RBAC на уровне проекта
3. **OAuth**: GitHub OAuth 2.0
4. **Webhooks**: HMAC подпись для GitHub webhooks
5. **SQL Injection**: SQLAlchemy ORM защищает
6. **XSS**: Валидация и санитизация контента

## Масштабируемость

### Текущая архитектура (модульный монолит)
- Все компоненты в одном приложении
- Легко разрабатывать и тестировать
- Простое развертывание

### Эволюция в микросервисы
Модули можно выделить в отдельные сервисы:
- **auth-service**: Аутентификация и авторизация
- **project-service**: Управление проектами
- **document-service**: Документация
- **git-service**: Git интеграция
- **ai-service**: AI обработка
- **notification-service**: Уведомления

## Следующие шаги

1. Настройка базовой инфраструктуры
2. Реализация доменных моделей
3. Миграции БД
4. API endpoints
5. Интеграции

