# Руководство по развертыванию DocuCraft

## Production развертывание

### Требования

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Nginx (рекомендуется)
- Systemd (для управления сервисами)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.11 python3.11-venv postgresql redis-server nginx git

# Создание пользователя для приложения
sudo useradd -m -s /bin/bash docucraft
sudo su - docucraft
```

### Шаг 2: Установка приложения

```bash
# Клонирование репозитория
git clone https://github.com/your-org/docucraft.git
cd docucraft

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
nano .env  # Настройте переменные окружения
```

### Шаг 3: Настройка базы данных

```bash
# Создание базы данных
sudo -u postgres createdb docucraft
sudo -u postgres createuser docucraft_user
sudo -u postgres psql -c "ALTER USER docucraft_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE docucraft TO docucraft_user;"

# Обновление DATABASE_URL в .env
# DATABASE_URL=postgresql+asyncpg://docucraft_user:secure_password@localhost/docucraft
```

### Шаг 4: Применение миграций

```bash
source venv/bin/activate
alembic upgrade head
```

### Шаг 5: Настройка Systemd сервисов

#### FastAPI сервис

`/etc/systemd/system/docucraft-api.service`:

```ini
[Unit]
Description=DocuCraft API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=docucraft
WorkingDirectory=/home/docucraft/docucraft
Environment="PATH=/home/docucraft/docucraft/venv/bin"
ExecStart=/home/docucraft/docucraft/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Celery worker

`/etc/systemd/system/docucraft-worker.service`:

```ini
[Unit]
Description=DocuCraft Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=docucraft
WorkingDirectory=/home/docucraft/docucraft
Environment="PATH=/home/docucraft/docucraft/venv/bin"
ExecStart=/home/docucraft/docucraft/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск сервисов:

```bash
sudo systemctl daemon-reload
sudo systemctl enable docucraft-api docucraft-worker
sudo systemctl start docucraft-api docucraft-worker
```

### Шаг 6: Настройка Nginx

`/etc/nginx/sites-available/docucraft`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/docucraft /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Шаг 7: SSL сертификат (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Шаг 8: Настройка бэкапов

Создайте скрипт для бэкапа БД:

`/home/docucraft/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/docucraft/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U docucraft_user docucraft > $BACKUP_DIR/db_backup_$DATE.sql
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
```

Добавьте в crontab:

```bash
crontab -e
# Добавьте строку:
0 2 * * * /home/docucraft/backup.sh
```

## Docker развертывание

### Docker Compose

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: docucraft
      POSTGRES_USER: docucraft
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql+asyncpg://docucraft:secure_password@db/docucraft
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - ./storage:/app/storage

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://docucraft:secure_password@db/docucraft
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN alembic upgrade head

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Запуск:

```bash
docker-compose up -d
```

## Мониторинг

### Логи

```bash
# API логи
sudo journalctl -u docucraft-api -f

# Worker логи
sudo journalctl -u docucraft-worker -f
```

### Health check

```bash
curl http://localhost:8000/health
```

### Метрики

Рекомендуется использовать:
- Prometheus для метрик
- Grafana для визуализации
- Sentry для отслеживания ошибок

## Безопасность

1. **Секретные ключи**: Никогда не коммитьте `.env` файл
2. **HTTPS**: Всегда используйте HTTPS в production
3. **Firewall**: Настройте firewall для ограничения доступа
4. **Обновления**: Регулярно обновляйте зависимости
5. **Бэкапы**: Настройте автоматические бэкапы БД

## Масштабирование

Для горизонтального масштабирования:

1. Используйте несколько экземпляров API за load balancer
2. Используйте несколько Celery workers
3. Настройте Redis Cluster для кеширования
4. Используйте PostgreSQL репликацию для чтения

