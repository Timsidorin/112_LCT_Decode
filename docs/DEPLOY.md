# Запуск на сервере (Docker)

Полный стек: **frontend**, **backend (API)**, **celery_worker**, **PostgreSQL**, **Redis**, **nginx**, **certbot**.

## Быстрый старт

```bash
# 1. Конфиг — backend/.env (секреты, S3, AI, Yandex)
cp backend/.env.example backend/.env   # если файла ещё нет
nano backend/.env

# 2. Опционально: симлинк для подстановки POSTGRES_* в compose
ln -sf backend/.env .env

# 3. Сборка и запуск
docker compose up -d --build

# 4. Проверка
docker compose ps
docker compose logs -f backend
docker compose logs -f celery_worker
```

> Все переменные — в **`backend/.env`**. Корневой `.env` не обязателен (только симлинк для compose).

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

## CI/CD из GitHub Actions

В репозитории добавлен workflow: `.github/workflows/deploy.yml`.

Он запускается при `push` в `main` (и вручную через `workflow_dispatch`) и выполняет на сервере:

```bash
docker compose down
docker compose up -d --build
```

### 1) Одноразово на сервере

```bash
# под пользователем деплоя
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cd /opt
git clone <ваш-repo-url> events_knastu
cd events_knastu
cp backend/.env.example backend/.env
nano backend/.env
docker compose up -d --build
```

### 2) Секреты в GitHub

Repo → Settings → Secrets and variables → Actions → New repository secret:

- `DEPLOY_HOST` — IP/домен сервера
- `DEPLOY_PORT` — обычно `22`
- `DEPLOY_USER` — пользователь на сервере (например `deploy`)
- `DEPLOY_SSH_KEY` — приватный SSH-ключ (целиком, включая `BEGIN/END`)
- `DEPLOY_PATH` — путь к репозиторию на сервере (например `/opt/events_knastu`)

### 3) Публичный ключ на сервер

Добавьте публичную часть ключа в `~/.ssh/authorized_keys` пользователя `DEPLOY_USER`.

Проверка:

```bash
ssh -i <private_key> <DEPLOY_USER>@<DEPLOY_HOST>
```

### 4) Триггер деплоя

Сделайте push в `main` — workflow сам подключится по SSH и выполнит пересборку.

Если нужен ручной запуск: GitHub → Actions → `Deploy To Server` → Run workflow.

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

Конфиг: **`backend/.env`**

| Переменные | Назначение |
|------------|------------|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL (должны совпадать с `DB_*`) |
| `REDIS_URL`, `CELERY_*` | В Docker лучше `redis://redis:6379/0` |
| `SECRET_KEY`, `AWS_*`, `S3_*`, `AI_*` | Backend |
| `YANDEX_*`, `FRONTEND_PUBLIC_URL` | OAuth |

Compose переопределяет для Docker: `DB_HOST=db`, `DB_PASS` из `POSTGRES_PASSWORD`.

Опционально: `ln -sf backend/.env .env` — чтобы compose подставлял `${POSTGRES_*}` из вашего файла.

**Важно:** `POSTGRES_PASSWORD` = пароль при создании volume `postgres_data` (обычно `admin`).

`DB_HOST=localhost` в `backend/.env` **игнорируется** — compose задаёт `DB_HOST=db`.

## SSL (Let's Encrypt)

Nginx ожидает сертификаты в `./certbot/conf`. Первичная выдача — стандартная процедура certbot с webroot `./certbot/www`. Конфиг nginx: `nginx/conf.d/default.conf` (домен `ai-csis.ru` — замените на свой).

## Troubleshooting

**Видео загружается, но шаги не создаются**
- Проверьте worker: `docker compose logs celery_worker`
- Redis: `docker compose exec redis redis-cli ping` → `PONG`
- S3 и AI ключи в `backend/.env`

**502 Bad Gateway на `/api/*` или WebSocket**

Nginx работает, **backend недоступен**. Проверьте:

```bash
docker compose ps
docker compose logs backend --tail 50
docker compose exec nginx-proxy wget -qO- http://backend:8001/ || echo "backend unreachable"
```

Если backend `Restarting` или `unhealthy` — сначала почините БД (см. выше `InvalidPasswordError`):

```bash
grep '^DB_' backend/.env
docker compose exec db psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'ВАШ_DB_PASS';"
docker compose up -d --build backend celery_worker
docker compose restart nginx-proxy
```

Когда backend `healthy`, API и `wss://.../api/ws/notifications` заработают.


**Worker падает при второй задаче (только dev на Windows)**
- Используйте `-P solo -c 1`; в Docker (Linux) это не требуется

**Backend unhealthy / Restarting (1)**

```bash
docker compose logs backend --tail 80
```

Частые причины:

1. **Пароль PostgreSQL не совпадает** — volume `postgres_data` хранит старый пароль. Если в `.env` сменили `POSTGRES_PASSWORD`, БД всё равно использует пароль при первом создании volume.

   ```bash
   grep POSTGRES_PASSWORD backend/.env
   grep DB_PASS backend/.env
   ```

   Пароль в `.env` (`POSTGRES_PASSWORD`) должен совпадать с тем, с которым volume был создан (раньше часто `admin`). Либо верните `POSTGRES_PASSWORD=admin`, либо пересоздайте volume (удалит данные!):

   ```bash
   docker compose down
   docker volume rm constructor_training_postgres_data
   docker compose up -d --build
   ```

2. **`backend/.env` переопределяет хост БД** — в Docker не задавайте `DB_HOST=localhost` в `backend/.env`. Хост задаёт `docker-compose.yml` (`DB_HOST=db`).

3. **Ошибка миграции Alembic** — в логах будет `alembic upgrade head`. Ручной прогон:

   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

Для отладки БД/Redis с хоста добавьте в `docker-compose.yml` проброс портов `5432` / `6379`.
