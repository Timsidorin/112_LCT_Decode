# Celery worker

Обработка видео идёт **только в worker**. Web-процесс (uvicorn) принимает файл, ставит задачу в Redis и сразу отвечает.

## Docker (production)

Worker поднимается сервисом `celery_worker` из корня репозитория:

```bash
docker compose up -d celery_worker
docker compose logs -f celery_worker
docker compose restart celery_worker
```

Подробнее: [docs/DEPLOY.md](../../docs/DEPLOY.md)

## Локально (два терминала)

**Терминал 1 — API (без `--reload`, иначе на Windows event loop может подвисать):**

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --host 0.0.0.0 --port 8002
```

**Терминал 2 — Worker:**

```bash
cd backend
uv sync
uv run celery -A core.celery_app worker --loglevel=info -c 1
```

На **Windows** (в `celery_app.py` уже `solo`):

```powershell
uv run celery -A core.celery_app worker --loglevel=info -P solo -c 1
```

Redis должен быть доступен (`redis://localhost:6379/0`).

## Переменные окружения

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

В Docker эти URL задаются в `docker-compose.yml` (`redis://redis:6379/0`).

## Очистка зависшей очереди

```bash
# Остановите worker, затем:
uv run python scripts/cleanup_stuck_tasks.py

# или в Docker:
docker compose exec celery_worker python scripts/cleanup_stuck_tasks.py
docker compose restart celery_worker
```

## Задачи

| Celery task | Описание |
|-------------|----------|
| `worker.tasks.process_training_video_task` | AI-разбор видео → шаги тренинга |
| `worker.tasks.process_media_task` | Общая обработка медиа (PDF и др.) |

Постановка в очередь из API: `core/task_queue.py` → `enqueue_process_training_video(task_id)`.
