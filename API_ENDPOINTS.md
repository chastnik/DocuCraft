# API Endpoints Reference

## Аутентификация

### POST /api/v1/auth/register
Регистрация нового пользователя.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

### POST /api/v1/auth/login
Вход в систему.

**Request Body (form-data):**
- username: email пользователя
- password: пароль

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### GET /api/v1/auth/me
Получение информации о текущем пользователе.

**Headers:**
- Authorization: Bearer {token}

## Проекты

### GET /api/v1/projects
Список всех проектов пользователя.

### POST /api/v1/projects
Создание нового проекта.

**Request Body:**
```json
{
  "name": "Project Name",
  "description": "Project description",
  "github_repo_url": "https://github.com/owner/repo",
  "ai_mode": "suggest-only"
}
```

### GET /api/v1/projects/{project_id}
Получение проекта по ID.

### PUT /api/v1/projects/{project_id}
Обновление проекта.

### DELETE /api/v1/projects/{project_id}
Удаление проекта.

### GET /api/v1/projects/{project_id}/members
Список участников проекта.

### POST /api/v1/projects/{project_id}/members
Добавление участника в проект.

**Request Body:**
```json
{
  "user_id": "user_uuid",
  "role": "Editor"
}
```

### PUT /api/v1/projects/{project_id}/members/{user_id}
Обновление роли участника.

### DELETE /api/v1/projects/{project_id}/members/{user_id}
Удаление участника из проекта.

## Документы

### GET /api/v1/documents/projects/{project_id}/documents
Список документов в проекте.

### POST /api/v1/documents/projects/{project_id}/documents
Создание документа.

**Request Body:**
```json
{
  "title": "Document Title",
  "slug": "document-slug",
  "content": "# Markdown content",
  "content_json": {}
}
```

### GET /api/v1/documents/{document_id}
Получение документа по ID.

### PUT /api/v1/documents/{document_id}
Обновление документа.

### DELETE /api/v1/documents/{document_id}
Удаление документа.

### GET /api/v1/documents/{document_id}/versions
Список версий документа.

### GET /api/v1/documents/{document_id}/versions/{version_number}
Получение конкретной версии документа.

## Git интеграция

### POST /api/v1/git/webhook/{project_id}
GitHub webhook endpoint.

**Headers:**
- X-GitHub-Event: тип события (push, pull_request, etc.)
- X-Hub-Signature-256: HMAC подпись

### GET /api/v1/git/projects/{project_id}/analyze/{commit_hash}
Анализ конкретного коммита.

### GET /api/v1/git/projects/{project_id}/commits
Список коммитов в репозитории.

**Query Parameters:**
- branch: ветка (по умолчанию "main")

## GitHub OAuth

### GET /api/v1/github/authorize
Перенаправление на GitHub OAuth авторизацию.

### GET /api/v1/github/callback
Callback для GitHub OAuth.

**Query Parameters:**
- code: код авторизации
- state: состояние (CSRF защита)

## AI предложения

### POST /api/v1/ai/documents/{document_id}/analyze
Анализ изменений кода и генерация предложений.

**Request Body:**
```json
{
  "diff": "git diff content",
  "commit_message": "Commit message",
  "files_changed": ["file1.py", "file2.js"],
  "project_id": "project_uuid",
  "git_event_id": "event_uuid"
}
```

### POST /api/v1/ai/suggestions/{suggestion_id}/approve
Утверждение и применение AI предложения.

### POST /api/v1/ai/suggestions/{suggestion_id}/reject
Отклонение AI предложения.

## OpenAPI интеграция

### POST /api/v1/openapi/projects/{project_id}/spec
Загрузка OpenAPI спецификации из файла.

**Request:**
- file: OpenAPI JSON/YAML файл
- git_commit_hash: (опционально) хеш коммита

### POST /api/v1/openapi/projects/{project_id}/spec/json
Загрузка OpenAPI спецификации как JSON.

**Request Body:**
```json
{
  "spec_content": { /* OpenAPI spec */ },
  "git_commit_hash": "commit_hash"
}
```

### GET /api/v1/openapi/projects/{project_id}/spec
Получение последней OpenAPI спецификации проекта.

### GET /api/v1/openapi/projects/{project_id}/spec/endpoints
Извлечение endpoints из OpenAPI спецификации.

### POST /api/v1/openapi/projects/{project_id}/spec/generate-docs
Генерация документации из OpenAPI спецификации.

### POST /api/v1/openapi/projects/{project_id}/spec/link/{document_id}
Связывание API endpoints с документацией.

## WebSocket

### WS /ws/documents/{document_id}?token={jwt_token}
WebSocket соединение для realtime редактирования документа.

**Сообщения от клиента:**

1. **content_change** - изменение контента
```json
{
  "type": "content_change",
  "changes": { /* изменения */ },
  "version": 1
}
```

2. **cursor_position** - позиция курсора
```json
{
  "type": "cursor_position",
  "position": { "line": 10, "column": 5 }
}
```

3. **selection** - выделение текста
```json
{
  "type": "selection",
  "selection": { "start": 0, "end": 100 }
}
```

4. **ping** - проверка соединения
```json
{
  "type": "ping"
}
```

**Сообщения от сервера:**

1. **document_state** - начальное состояние документа
```json
{
  "type": "document_state",
  "content": "# Document content",
  "version": 1
}
```

2. **active_users** - список активных пользователей
```json
{
  "type": "active_users",
  "users": ["user_id_1", "user_id_2"]
}
```

3. **content_change** - изменение контента от другого пользователя
```json
{
  "type": "content_change",
  "user_id": "user_uuid",
  "changes": { /* изменения */ },
  "version": 2
}
```

4. **user_joined** - пользователь присоединился
```json
{
  "type": "user_joined",
  "user_id": "user_uuid",
  "message": "User joined the document"
}
```

5. **user_left** - пользователь покинул
```json
{
  "type": "user_left",
  "user_id": "user_uuid",
  "message": "User left the document"
}
```

6. **pong** - ответ на ping
```json
{
  "type": "pong"
}
```

## Роли и права доступа

### Viewer
- Просмотр проектов и документов
- Просмотр версий документов

### Editor
- Все права Viewer
- Создание и редактирование документов
- Удаление документов

### ProjectLead
- Все права Editor
- Утверждение AI предложений
- Управление участниками проекта (кроме удаления)

### Admin
- Все права ProjectLead
- Полное управление проектом
- Удаление участников
- Изменение настроек проекта

