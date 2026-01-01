# DocuCraft

Сервис для автоматической генерации и сопровождения документации по ИТ-проектам.

## Описание

DocuCraft — это enterprise-level SaaS-продукт, который:
- Подключается к git-репозиториям проектов
- Анализирует изменения в коде
- Предлагает и применяет обновления документации
- Поддерживает совместную работу нескольких пользователей

## Технологический стек

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery
- **Frontend**: React, TypeScript, TipTap, Tailwind CSS (планируется)

## Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Poetry (для управления зависимостями) или pip

### Автоматическая установка

```bash
# Запустите скрипт установки
./scripts/setup.sh
```

### Ручная установка

1. Клонируйте репозиторий
2. Установите зависимости:
```bash
poetry install
# или
pip install -r requirements.txt
```

3. Скопируйте `.env.example` в `.env` и настройте переменные окружения

4. Создайте базу данных:
```bash
createdb docucraft
```

5. Примените миграции:
```bash
alembic upgrade head
```

6. Запустите приложение:
```bash
# Автоматический запуск (включает Celery)
./scripts/start.sh

# Или вручную:
uvicorn app.main:app --reload

# В отдельном терминале для Celery:
celery -A app.tasks.celery_app worker --loglevel=info
```

## Архитектура

Подробное описание архитектуры см. в [ARCHITECTURE.md](./ARCHITECTURE.md)

## API документация

После запуска приложения API документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Документация

- [Архитектура](./ARCHITECTURE.md) - Подробное описание архитектуры
- [API Endpoints](./API_ENDPOINTS.md) - Справочник всех API endpoints
- [Примеры использования](./EXAMPLES.md) - Примеры запросов и интеграций
- [Статус реализации](./IMPLEMENTATION_STATUS.md) - Текущий статус проекта
- [Функции](./FEATURES.md) - Список реализованных функций

## Разработка

### Структура проекта

```
app/
├── api/          # HTTP endpoints и WebSockets
├── domain/       # Бизнес-логика (модели, сервисы, репозитории)
├── infrastructure/ # БД, внешние сервисы (GitHub, AI)
├── core/         # Конфигурация, безопасность, валидация
└── tasks/        # Celery задачи
```

### Тестирование

```bash
pytest
```

### Линтинг

```bash
black .
ruff check .
mypy .
```

### Переменные окружения

Основные переменные в `.env`:

- `DATABASE_URL` - URL базы данных PostgreSQL
- `SECRET_KEY` - Секретный ключ для JWT
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` - API ключи AI провайдеров
- `REDIS_URL` - URL Redis для кеширования и Celery

## Лицензия

MIT

