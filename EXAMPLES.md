# Примеры использования DocuCraft API

## Быстрый старт

### 1. Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

**Ответ:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Вход в систему

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Создание проекта

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Awesome Project",
    "description": "Project description",
    "github_repo_url": "https://github.com/owner/repo",
    "ai_mode": "suggest-only"
  }'
```

### 4. Создание документа

```bash
curl -X POST "http://localhost:8000/api/v1/documents/projects/PROJECT_ID/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Getting Started",
    "slug": "getting-started",
    "content": "# Getting Started\n\nWelcome to the project!",
    "content_json": null
  }'
```

## Работа с GitHub

### Настройка webhook

1. Перейдите в настройки репозитория GitHub
2. Webhooks → Add webhook
3. URL: `http://your-domain.com/api/v1/git/webhook/PROJECT_ID`
4. Content type: `application/json`
5. Secret: сгенерируйте секретный ключ и сохраните в настройках проекта

### Анализ коммита

```bash
curl -X GET "http://localhost:8000/api/v1/git/projects/PROJECT_ID/analyze/COMMIT_HASH" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ответ:**
```json
{
  "commit_hash": "abc123...",
  "message": "Add new feature",
  "author": "John Doe",
  "files_changed": ["src/main.py", "src/utils.py"],
  "code_changes": {
    "added_lines": 50,
    "removed_lines": 10,
    "functions_changed": ["process_data"],
    "classes_changed": []
  },
  "affected_documents": [
    {
      "document_id": "doc-uuid",
      "title": "API Documentation",
      "slug": "api-docs",
      "reason": "File src/main.py might be related"
    }
  ]
}
```

## Работа с AI

### Генерация предложений

```bash
curl -X POST "http://localhost:8000/api/v1/ai/documents/DOCUMENT_ID/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "diff --git a/src/main.py...",
    "commit_message": "Add new endpoint",
    "files_changed": ["src/main.py"],
    "project_id": "PROJECT_ID"
  }'
```

**Ответ:**
```json
{
  "suggestions": [
    {
      "id": "suggestion-uuid",
      "type": "update",
      "target_section": "API Endpoints",
      "status": "pending"
    }
  ]
}
```

### Утверждение предложения

```bash
curl -X POST "http://localhost:8000/api/v1/ai/suggestions/SUGGESTION_ID/approve" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Работа с OpenAPI

### Загрузка спецификации

```bash
curl -X POST "http://localhost:8000/api/v1/openapi/projects/PROJECT_ID/spec" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@openapi.json" \
  -F "git_commit_hash=abc123"
```

### Генерация документации

```bash
curl -X POST "http://localhost:8000/api/v1/openapi/projects/PROJECT_ID/spec/generate-docs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ответ:**
```json
{
  "sections": [
    {
      "title": "API Overview",
      "content": "# API\n\n..."
    },
    {
      "title": "Users",
      "content": "## Users\n\n..."
    }
  ]
}
```

## WebSocket соединение

### JavaScript пример

```javascript
const token = 'YOUR_JWT_TOKEN';
const documentId = 'DOCUMENT_ID';
const ws = new WebSocket(`ws://localhost:8000/ws/documents/${documentId}?token=${token}`);

ws.onopen = () => {
  console.log('Connected to document');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'document_state':
      console.log('Document content:', message.content);
      break;
    case 'content_change':
      console.log('Content changed by:', message.user_id);
      applyChanges(message.changes);
      break;
    case 'user_joined':
      console.log('User joined:', message.user_id);
      break;
    case 'user_left':
      console.log('User left:', message.user_id);
      break;
  }
};

// Отправка изменений
function sendContentChange(changes) {
  ws.send(JSON.stringify({
    type: 'content_change',
    changes: changes,
    version: currentVersion
  }));
}

// Отправка позиции курсора
function sendCursorPosition(line, column) {
  ws.send(JSON.stringify({
    type: 'cursor_position',
    position: { line, column }
  }));
}
```

### Python пример

```python
import asyncio
import websockets
import json

async def connect_to_document(document_id, token):
    uri = f"ws://localhost:8000/ws/documents/{document_id}?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Получение начального состояния
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Document state: {data}")
        
        # Отправка изменений
        await websocket.send(json.dumps({
            "type": "content_change",
            "changes": {"insert": "new text"},
            "version": 1
        }))
        
        # Прослушивание сообщений
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# Использование
asyncio.run(connect_to_document("doc-id", "your-token"))
```

## Интеграция с CI/CD

### GitHub Actions пример

```yaml
name: Update Documentation

on:
  push:
    branches: [main]

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Get commit hash
        id: commit
        run: echo "hash=$(git rev-parse HEAD)" >> $GITHUB_OUTPUT
      
      - name: Trigger documentation update
        run: |
          curl -X POST "${{ secrets.DOCUCRAFT_URL }}/api/v1/git/projects/${{ secrets.PROJECT_ID }}/analyze/${{ steps.commit.outputs.hash }}" \
            -H "Authorization: Bearer ${{ secrets.DOCUCRAFT_TOKEN }}"
```

## Обработка ошибок

Все endpoints возвращают стандартные HTTP коды:

- `200` - Успешно
- `201` - Создано
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `409` - Конфликт (например, дублирующийся slug)
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

**Пример ответа с ошибкой:**
```json
{
  "detail": "Document with this slug already exists in the project"
}
```

