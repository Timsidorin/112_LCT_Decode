# Запуск на сервере (Docker)

Полный стек: **frontend**, **backend (API)**, **celery_worker**, **PostgreSQL**, **Redis**, **nginx**, **certbot**.

## Быстрый старт

```bash
# 1. Переменные инфраструктуры (PostgreSQL)
cp .env.example .env
# отредактируйте POSTGRES_PASSWORD

# 2. Секреты приложения (S3, AI, JWT)
cp backend/.env.example backend/.env
# заполните SECRET_KEY, AWS_*, AI_API_KEY и т.д.

# 3. Сборка и запуск
docker compose up -d --build

# 4. Проверка
docker compose ps
docker compose logs -f celery_worker
docker compose logs -f backend
```

После старта:
- Сайт: `https://<ваш-домен>/` (через nginx)
- API: `https://<ваш-домен>/api/`
- WebSocket уведомлений: `wss://<ваш-домен>/api/ws/notifications`

## Сервисы

| Сервис | Назначение |
|--------|------------|
| `backend` | FastAPI (uvicorn :8001), миграции Alembic при старте |
| `celery_worker` | Фоновая обработка видео (AI + S3) |
| `redis` | Брокер Celery + pub/sub для WebSocket |
| `db` | PostgreSQL 15 |
| `frontend` | Статика Vue (nginx внутри контейнера) |
| `nginx` | Reverse proxy, SSL, `/api/` → backend |

## Celery worker

В Docker worker запускается автоматически сервисом `celery_worker`:

```bash
docker compose up -d celery_worker
docker compose logs -f celery_worker
docker compose restart celery_worker
```

Команда внутри контейнера (Linux, prefork, 1 процесс):

```bash
celery -A core.celery_app worker --loglevel=info --concurrency=1 --hostname=worker@%h
```

На Windows в dev используйте `-P solo -c 1` (см. `run_celery_worker.md`).

### Очистка зависших задач

```bash
docker compose exec celery_worker python scripts/cleanup_stuck_tasks.py
docker compose restart celery_worker
```

## Обновление после git pull

```bash
git pull
docker compose up -d --build
# миграции применяются при рестарте backend (alembic upgrade head)
```

## Локальная разработка без Docker

Два терминала + Redis локально:

**API:**
```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --host 0.0.0.0 --port 8002
```

**Worker:**
```bash
cd backend
uv run celery -A core.celery_app worker --loglevel=info -P solo -c 1   # Windows
# uv run celery -A core.celery_app worker --loglevel=info -c 1         # Linux/macOS
```

## Переменные окружения

### Корень `.env` (docker-compose)

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `LOG_LEVEL` (опционально)
- `DOMAIN` (для документации SSL)

### `backend/.env`

Секреты и внешние сервисы. В Docker **переопределяются** из compose:
- `DB_HOST=db`
- `REDIS_URL=redis://redis:6379/0`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

Обязательно задайте в `backend/.env`:
- `SECRET_KEY`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `S3_ENDPOINT_URL`
- `AI_API_KEY`

## SSL (Let's Encrypt)

Nginx ожидает сертификаты в `./certbot/conf`. Первичная выдача — стандартная процедура certbot с webroot `./certbot/www`. Конфиг nginx: `nginx/conf.d/default.conf` (домен `ai-csis.ru` — замените на свой).

## Troubleshooting

**Видео загружается, но шаги не создаются**
- Проверьте worker: `docker compose logs celery_worker`
- Redis: `docker compose exec redis redis-cli ping` → `PONG`
- S3 и AI ключи в `backend/.env`

**WebSocket не подключается**
- Nginx проксирует `/api/` с заголовками Upgrade (см. `nginx/conf.d/default.conf`)
- Frontend в production собирается с `VITE_API_BASE_URL=/api`

**Worker падает при второй задаче (только dev на Windows)**
- Используйте `-P solo -c 1`; в Docker (Linux) это не требуется

**Порты 5432/6379 снаружи не проброшены** — так безопаснее на сервере. Для отладки добавьте в `docker-compose.yml`:

```yaml
db:
  ports:
    - "5432:5432"
redis:
  ports:
    - "6379:6379"
```
