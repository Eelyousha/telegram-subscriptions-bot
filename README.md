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

- Python 3.12+
- Podman (или Docker)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### Запуск через Podman Compose

```bash
# Создать .env файл
cp .env.example .env
# Отредактировать .env, добавив BOT_TOKEN и настройки БД

# Запустить все сервисы
cd deploy
podman-compose up -d
```

### Локальный запуск (разработка)

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Поднять PostgreSQL (или использовать существующий)
podman run -d --name postgres \
  -e POSTGRES_USER=subscriptions \
  -e POSTGRES_PASSWORD=subscriptions \
  -e POSTGRES_DB=subscriptions \
  -p 5432:5432 postgres:16-alpine

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

## Мониторинг

После запуска доступны:

- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Метрики API**: http://localhost:8000/metrics

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
