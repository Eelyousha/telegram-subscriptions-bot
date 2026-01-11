# telegram-subscriptions-bot
Telegram bot to track your subscriptions and pay dates all-in-one-place

# Subscription Tracker

Сервис для учёта подписок на различные сервисы. Позволяет отслеживать регулярные платежи, получать уведомления перед списанием и анализировать расходы на подписки.

## Архитектура

```
┌─────────────┐     HTTP/JSON    ┌─────────────┐     SQLAlchemy    ┌────────────┐
│  Telegram   │ ◄──────────────► │   FastAPI   │ ◄───────────────► │ PostgreSQL │
│     Bot     │                  │     API     │                   │            │
└─────────────┘                  └─────────────┘                   └────────────┘
   Контейнер 1                      Контейнер 2                      Контейнер 3
```

- **API** (FastAPI) — бизнес-логика, работа с БД, планировщик уведомлений
- **Bot** (aiogram) — Telegram-интерфейс, взаимодействует с API по HTTP
- **PostgreSQL** — хранение данных

## Возможности

- 📝 **Управление подписками** — добавление, редактирование и удаление подписок
- 💰 **Учёт расходов** — отслеживание сумм и валют (RUB, USD, EUR)
- 🔔 **Уведомления** — напоминания за N дней до списания
- 📊 **Статистика** — общая сумма расходов, количество подписок, ближайшие платежи
- 📈 **Мониторинг** — метрики Prometheus + дашборды Grafana

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы, справка |
| `/add` | Добавить новую подписку |
| `/list` | Список всех активных подписок |
| `/stats` | Статистика расходов |
| `/edit` | Редактировать подписку |
| `/delete` | Удалить подписку |

## Быстрый старт

### Требования

- Python 3.11+
- Docker или Podman
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### Запуск через Docker Compose

```bash
# Создать .env файл
cat > .env << EOF
BOT_TOKEN=your_telegram_bot_token_here
NOTIFICATION_HOUR=10
LOG_LEVEL=INFO
LOG_FORMAT=json
THROTTLE_RATE=30
EOF

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
docker-compose logs -f
```

### Запуск через Podman Compose

```bash
# Создать .env файл (см. выше)

# Запустить все сервисы
cd deploy
podman-compose -f podman-compose.yml up -d
```

### Локальный запуск (разработка)

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://subscriptions_user:subscriptions_pass@localhost:5432/subscriptions
BOT_TOKEN=your_telegram_bot_token
API_URL=http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000
NOTIFICATION_HOUR=10
LOG_LEVEL=DEBUG
LOG_FORMAT=console
THROTTLE_RATE=30
EOF

# Поднять PostgreSQL
docker run -d --name subscriptions-db \
  -e POSTGRES_DB=subscriptions \
  -e POSTGRES_USER=subscriptions_user \
  -e POSTGRES_PASSWORD=subscriptions_pass \
  -p 5432:5432 postgres:16-alpine

# Применить миграции
alembic upgrade head

# Запустить API
python -m src.api.main

# В другом терминале — запустить бота
python -m src.bot.main
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/users` | Создать/обновить пользователя |
| `GET` | `/users/{telegram_id}/subscriptions` | Список подписок пользователя |
| `POST` | `/users/{telegram_id}/subscriptions` | Создать подписку |
| `GET` | `/subscriptions/{id}` | Получить подписку |
| `PATCH` | `/subscriptions/{id}` | Обновить подписку |
| `DELETE` | `/subscriptions/{id}` | Удалить подписку |
| `GET` | `/users/{telegram_id}/stats` | Статистика пользователя |
| `GET` | `/health` | Healthcheck |
| `GET` | `/metrics` | Prometheus метрики |

Документация API: http://localhost:8000/docs

## Миграции базы данных

```bash
# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Откатить миграцию
alembic downgrade -1

# Просмотр истории
alembic history
```

## Мониторинг

После запуска доступны:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Метрики Prometheus**: http://localhost:8000/metrics

### Метрики

**Бизнес-метрики:**
- `subscriptions_total` - количество активных подписок
- `subscriptions_monthly_amount_rub` - сумма подписок в месяц (RUB)
- `users_total` - общее количество пользователей
- `bot_active_users_24h` - активные пользователи за 24 часа

**Технические метрики:**
- `bot_commands_total` - количество обработанных команд
- `bot_command_duration_seconds` - время выполнения команд
- `db_operations_total` - операции с БД
- `notifications_sent_total` - отправленные уведомления

## Структура проекта

```
subscription-tracker/
├── src/
│   ├── api/                # FastAPI приложение
│   │   ├── main.py        # Точка входа API
│   │   ├── routes/        # Эндпоинты
│   │   ├── schemas.py     # Pydantic модели (request/response)
│   │   └── dependencies.py
│   ├── bot/               # Telegram бот
│   │   ├── main.py        # Точка входа бота
│   │   ├── handlers/      # Обработчики команд
│   │   ├── keyboards.py   # Клавиатуры
│   │   ├── states.py      # FSM состояния
│   │   └── api_client.py  # HTTP-клиент для API
│   ├── core/              # Общий код
│   │   ├── config.py      # Настройки
│   │   └── logging.py     # Логирование
│   ├── db/                # База данных
│   │   ├── models.py      # SQLAlchemy модели
│   │   ├── database.py    # Подключение
│   │   └── repository.py  # CRUD операции
│   ├── scheduler/         # Планировщик уведомлений
│   └── metrics/           # Prometheus метрики
├── deploy/
│   ├── Containerfile.api  # Образ API
│   ├── Containerfile.bot  # Образ бота
│   ├── compose.yml        # Podman Compose
│   └── prometheus.yml
├── alembic/               # Миграции БД
├── tests/
├── .env.example
└── requirements.txt
```

## Технологии

- **FastAPI** — REST API
- **SQLAlchemy 2.0** — ORM (async)
- **PostgreSQL 16** — база данных
- **aiogram 3.x** — Telegram Bot API
- **httpx** — async HTTP-клиент (бот → API)
- **APScheduler** — планировщик задач
- **Alembic** — миграции БД
- **structlog** — структурированное логирование
- **prometheus-client** — метрики
- **Pydantic** — валидация и настройки

## Конфигурация

Все настройки задаются через переменные окружения:

| Переменная | Описание | По умолчанию | Обязательна |
|------------|----------|--------------|-------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | - | ✅ |
| `BOT_TOKEN` | Токен Telegram бота | - | ✅ |
| `API_URL` | URL API сервера (для бота) | `http://api:8000` | |
| `API_HOST` | Хост API сервера | `0.0.0.0` | |
| `API_PORT` | Порт API сервера | `8000` | |
| `NOTIFICATION_HOUR` | Час отправки уведомлений (UTC) | `10` | |
| `LOG_LEVEL` | Уровень логирования (DEBUG, INFO, WARNING, ERROR) | `INFO` | |
| `LOG_FORMAT` | Формат логов (json, console) | `json` | |
| `THROTTLE_RATE` | Лимит сообщений в минуту на пользователя | `30` | |

## Логирование

Сервис использует структурированное логирование (structlog).

**Форматы:**
- `json` - JSON формат (рекомендуется для продакшена)
- `console` - читаемый формат для разработки

**Уровни:**
- `DEBUG` - детальная информация для отладки
- `INFO` - общая информация о работе сервиса
- `WARNING` - предупреждения
- `ERROR` - ошибки

## Тестирование

```bash
# Установить зависимости для тестирования
pip install -r requirements.txt

# Запустить все тесты
pytest

# Запустить с покрытием
pytest --cov=src tests/

# Запустить конкретный тест
pytest tests/test_api/test_subscriptions.py -v
```

## Планировщик уведомлений

Планировщик работает в контейнере API и выполняет задачи по расписанию:

1. **Отправка уведомлений** - ежедневно в `NOTIFICATION_HOUR` (UTC)
   - Находит подписки, до оплаты которых осталось N дней
   - Отправляет уведомления пользователям в Telegram

2. **Обновление дат** - через час после уведомлений
   - Переносит прошедшие даты оплаты на следующий период

## Разработка

### Добавление новой команды бота

1. Создайте обработчик в `src/bot/handlers/`
2. При необходимости добавьте состояния FSM в `src/bot/states.py`
3. Добавьте клавиатуры в `src/bot/keyboards.py`
4. Зарегистрируйте роутер в `src/bot/main.py`

### Добавление нового API endpoint

1. Создайте роут в `src/api/routes/`
2. Добавьте схемы Pydantic в `src/api/schemas.py`
3. При необходимости обновите репозитории в `src/db/repository.py`
4. Зарегистрируйте роутер в `src/api/main.py`

### Изменение схемы БД

1. Обновите модели в `src/db/models.py`
2. Создайте миграцию: `alembic revision --autogenerate -m "description"`
3. Проверьте сгенерированную миграцию в `alembic/versions/`
4. Примените миграцию: `alembic upgrade head`

## Лицензия

MIT
