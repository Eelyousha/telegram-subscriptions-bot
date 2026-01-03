# Техническое задание: Subscription Tracker

## 1. Общее описание

**Название проекта**: Subscription Tracker

**Назначение**: Сервис для персонального учёта подписок на различные сервисы (стриминг, облачные хранилища, SaaS и т.д.). Позволяет пользователям вести учёт регулярных платежей, получать уведомления перед списанием и анализировать свои расходы на подписки.

**Тип проекта**: Pet-проект, не production-решение

**Целевая аудитория**: Несколько пользователей (личное использование автором и знакомыми)

## 1.1. Архитектура системы

Система состоит из трёх независимых компонентов:

```
┌─────────────────┐      HTTP/JSON       ┌─────────────────┐      SQLAlchemy      ┌────────────────┐
│                 │                      │                 │                      │                │
│  Telegram Bot   │ ◄──────────────────► │   FastAPI API   │ ◄──────────────────► │   PostgreSQL   │
│   (aiogram)     │                      │                 │                      │                │
│                 │                      │  + Scheduler    │                      │                │
└─────────────────┘                      └─────────────────┘                      └────────────────┘
    Контейнер 1                              Контейнер 2                              Контейнер 3
```

**Принципы разделения**:
- **API** — вся бизнес-логика, валидация, работа с БД, планировщик уведомлений
- **Bot** — только Telegram-интерфейс, преобразование команд в API-вызовы
- **PostgreSQL** — персистентное хранение данных

**Преимущества такой архитектуры**:
- Бот можно заменить на другой интерфейс (web, CLI) без изменения логики
- API можно масштабировать независимо от бота
- Легко тестировать API без Telegram
- Чёткое разделение ответственности

## 2. Функциональные требования

### 2.1. Управление подписками

#### Добавление подписки (`/add`)

Бот должен собирать следующую информацию через пошаговый диалог:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `name` | string | Да | Название сервиса (например, "Netflix", "Spotify") |
| `amount` | float | Да | Сумма списания |
| `currency` | enum | Да | Валюта: RUB, USD, EUR (по умолчанию RUB) |
| `period` | enum | Да | Периодичность: неделя (7 дней), месяц (30 дней), год (365 дней), произвольное кол-во дней |
| `next_payment` | date | Да | Дата следующего списания |
| `notify_days` | int | Нет | За сколько дней уведомлять (по умолчанию 3) |

**Сценарий диалога**:
```
Пользователь: /add
Бот: 📝 Введите название сервиса
Пользователь: Netflix
Бот: 💰 Введите сумму списания
Пользователь: 999
Бот: 💱 Выберите валюту [RUB] [USD] [EUR]
Пользователь: [RUB]
Бот: 🔄 Как часто списывается? [Неделя] [Месяц] [Год] [Другое]
Пользователь: [Месяц]
Бот: 📅 Введите дату следующего списания (ДД.ММ.ГГГГ) или нажмите "Сегодня"
Пользователь: 15.02.2025
Бот: 🔔 За сколько дней напомнить? (по умолчанию 3)
Пользователь: 3
Бот: ✅ Подписка добавлена!
     Netflix — 999 ₽/мес
     Следующее списание: 15.02.2025
     Напомню за 3 дня
```

**Валидация**:
- `amount` > 0
- `next_payment` >= сегодня
- `notify_days` >= 0 и <= `period`
- `name` — непустая строка, максимум 100 символов

#### Просмотр списка подписок (`/list`)

Выводит все активные подписки пользователя в формате:

```
📋 Ваши подписки (5):

1. Netflix — 999 ₽/мес
   Следующее списание: 15.02.2025 (через 12 дней)

2. Spotify — 199 ₽/мес
   Следующее списание: 20.02.2025 (через 17 дней)

3. iCloud — 2.99 $/мес
   Следующее списание: 01.03.2025 (через 26 дней)
```

Если подписок нет: "У вас пока нет подписок. Добавьте первую командой /add"

#### Редактирование подписки (`/edit`)

1. Показать список подписок с inline-кнопками для выбора
2. После выбора показать текущие значения и кнопки для редактирования каждого поля
3. При редактировании поля — запустить мини-диалог для ввода нового значения
4. После изменения вернуться к меню редактирования

#### Удаление подписки (`/delete`)

1. Показать список подписок с inline-кнопками
2. После выбора запросить подтверждение: "Удалить подписку Netflix? [Да] [Нет]"
3. При подтверждении — пометить подписку как неактивную (soft delete)

### 2.2. Статистика (`/stats`)

Выводит сводную информацию:

```
📊 Статистика подписок

Всего активных: 5
Общая сумма в месяц: ~1 847 ₽

💳 По валютам:
• RUB: 1 198 ₽/мес
• USD: $7.98/мес (~649 ₽)

📅 Ближайшие списания:
• 15.02 — Netflix (999 ₽)
• 20.02 — Spotify (199 ₽)
• 01.03 — iCloud ($2.99)
```

**Логика расчёта**:
- Все суммы приводятся к месячному эквиваленту (годовая / 12, недельная * 4.33)
- Курсы валют: фиксированные или через внешний API (опционально)
- "Ближайшие списания" — до 5 подписок в ближайшие 30 дней

### 2.3. Уведомления

#### Напоминания о списании

Уведомления отправляются **из API-сервиса** (не из бота), так как там работает планировщик и есть доступ к БД.

**Архитектура отправки уведомлений**:
```
┌─────────────┐     APScheduler      ┌─────────────┐    Telegram API    ┌──────────┐
│  PostgreSQL │ ◄──────────────────► │   FastAPI   │ ─────────────────► │ Telegram │
│             │   (читает подписки)  │ + Scheduler │   (отправляет)     │          │
└─────────────┘                      └─────────────┘                    └──────────┘
```

API-сервис имеет доступ к `BOT_TOKEN` и использует Telegram Bot API напрямую (через `aiogram` или `httpx`) для отправки сообщений.

**Логика работы**:
- APScheduler запускает задачу ежедневно в заданное время (по умолчанию 10:00)
- Задача запрашивает из БД подписки, где `next_payment - notify_days <= today`
- Для каждой подписки отправляет сообщение пользователю через Telegram API
- Формат сообщения:
  ```
  🔔 Напоминание о подписке
  
  Netflix — 999 ₽
  Списание через 3 дня (15.02.2025)
  ```

#### Обновление даты после списания

Отдельная задача APScheduler (ежедневно, после уведомлений):
- Находит подписки, где `next_payment < today`
- Автоматически пересчитывает `next_payment += period_days`
- Не отправляет уведомление о пересчёте

```python
# src/scheduler/notifications.py (псевдокод)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=settings.notification_hour)
async def send_notifications():
    bot = Bot(token=settings.bot_token)
    subscriptions = await repo.get_pending_notifications(date.today())
    
    for sub in subscriptions:
        text = f"🔔 Напоминание о подписке\n\n{sub.name} — {sub.amount} {sub.currency}\nСписание через {days_left} дней ({sub.next_payment})"
        await bot.send_message(chat_id=sub.telegram_id, text=text)
    
    await bot.session.close()

@scheduler.scheduled_job('cron', hour=settings.notification_hour + 1)
async def advance_payments():
    await repo.advance_past_payments()
```

### 2.4. Стартовое сообщение (`/start`)

```
👋 Привет! Я помогу отслеживать твои подписки.

Что я умею:
• /add — добавить подписку
• /list — список подписок
• /stats — статистика расходов
• /edit — редактировать подписку
• /delete — удалить подписку

Начни с добавления первой подписки: /add
```

## 3. Нефункциональные требования

### 3.1. Производительность

- Бот должен обрабатывать запросы от нескольких одновременных пользователей
- Время ответа на команду: < 2 секунды в 95% случаев
- Планировщик уведомлений не должен блокировать обработку команд

### 3.2. Надёжность

- Graceful shutdown при SIGTERM (корректное завершение для Podman)
- Автоматический переподъём при падении (restart policy в compose)
- Сохранение данных при перезапуске (persistent volume для SQLite)

### 3.3. Мониторинг

#### Метрики (Prometheus)

**Бизнес-метрики**:
| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `subscriptions_total` | Gauge | — | Общее количество активных подписок |
| `subscriptions_monthly_amount_rub` | Gauge | — | Общая сумма подписок в месяц (в рублях) |
| `users_total` | Gauge | — | Количество пользователей |

**Технические метрики**:
| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `bot_commands_total` | Counter | `command`, `status` | Количество обработанных команд |
| `bot_command_duration_seconds` | Histogram | `command` | Время обработки команды |
| `bot_active_users_24h` | Gauge | — | Активные пользователи за 24 часа |
| `db_operations_total` | Counter | `operation`, `status` | Операции с БД |
| `notifications_sent_total` | Counter | `status` | Отправленные уведомления |

#### Логирование

- Формат: JSON (structlog)
- Уровни: DEBUG, INFO, WARNING, ERROR
- Обязательные поля в каждой записи:
  - `timestamp` (ISO 8601)
  - `level`
  - `event` (название события)
  - `user_id` (если применимо)

**Примеры событий для логирования**:
- `command_received` — получена команда
- `command_completed` — команда выполнена
- `command_failed` — ошибка выполнения
- `subscription_created` — создана подписка
- `subscription_deleted` — удалена подписка
- `notification_sent` — отправлено уведомление
- `notification_failed` — ошибка отправки уведомления
- `db_error` — ошибка базы данных
- `scheduler_tick` — срабатывание планировщика

### 3.4. Безопасность

- Токен бота хранится в переменных окружения, не в коде
- Пользователь имеет доступ только к своим подпискам
- Rate limiting: не более 30 сообщений в минуту от одного пользователя

## 4. Техническая архитектура

### 4.1. Стек технологий

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Язык | Python | 3.12+ |
| API Framework | FastAPI | 0.110+ |
| ORM | SQLAlchemy | 2.0+ |
| База данных | PostgreSQL | 16 |
| Async DB driver | asyncpg | latest |
| Миграции | Alembic | latest |
| Telegram API | aiogram | 3.x |
| HTTP-клиент | httpx | latest |
| Планировщик | APScheduler | 3.x |
| Логирование | structlog | latest |
| Метрики | prometheus-client | latest |
| Конфигурация | pydantic-settings | latest |
| Контейнеризация | Podman | latest |

### 4.2. Структура проекта

```
subscription-tracker/
├── src/
│   ├── __init__.py
│   ├── api/                        # FastAPI приложение
│   │   ├── __init__.py
│   │   ├── main.py                 # Точка входа API
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── users.py            # /users endpoints
│   │   │   ├── subscriptions.py    # /subscriptions endpoints
│   │   │   └── health.py           # /health, /metrics
│   │   ├── schemas.py              # Pydantic модели (request/response)
│   │   ├── dependencies.py         # DI (get_db, get_repository)
│   │   └── exceptions.py           # HTTP exceptions
│   ├── bot/                        # Telegram бот
│   │   ├── __init__.py
│   │   ├── main.py                 # Точка входа бота
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py            # /start
│   │   │   ├── add.py              # /add (FSM диалог)
│   │   │   ├── list.py             # /list
│   │   │   ├── stats.py            # /stats
│   │   │   ├── edit.py             # /edit
│   │   │   └── delete.py           # /delete
│   │   ├── keyboards.py            # Inline и Reply клавиатуры
│   │   ├── states.py               # FSM состояния
│   │   ├── middlewares.py          # Logging, Throttling
│   │   └── api_client.py           # HTTP-клиент для API
│   ├── core/                       # Общий код
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings
│   │   └── logging.py              # Настройка structlog
│   ├── db/                         # База данных
│   │   ├── __init__.py
│   │   ├── database.py             # Engine, SessionLocal
│   │   ├── models.py               # SQLAlchemy модели
│   │   └── repository.py           # CRUD операции
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── notifications.py        # APScheduler задачи
│   └── metrics/
│       ├── __init__.py
│       └── prometheus.py           # Определение метрик
├── alembic/                        # Миграции
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── deploy/
│   ├── Containerfile.api           # Образ API
│   ├── Containerfile.bot           # Образ бота
│   ├── compose.yml                 # Podman Compose
│   └── prometheus.yml
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Фикстуры pytest
│   ├── test_api/
│   │   ├── test_subscriptions.py
│   │   └── test_users.py
│   └── test_bot/
│       └── test_handlers.py
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 4.3. Схема базы данных (PostgreSQL + SQLAlchemy)

```python
# src/db/models.py
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    period_days: Mapped[int] = mapped_column(Integer)
    next_payment: Mapped[date] = mapped_column(Date, index=True)
    notify_days: Mapped[int] = mapped_column(Integer, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates="subscriptions")
    
    __table_args__ = (
        Index("idx_subscriptions_active_payment", "telegram_id", "is_active", "next_payment"),
    )
```

**SQL эквивалент** (для понимания):
```sql
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'RUB',
    period_days INTEGER NOT NULL,
    next_payment DATE NOT NULL,
    notify_days INTEGER NOT NULL DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_telegram_id ON subscriptions(telegram_id);
CREATE INDEX idx_subscriptions_next_payment ON subscriptions(next_payment);
CREATE INDEX idx_subscriptions_active_payment ON subscriptions(telegram_id, is_active, next_payment);
```

### 4.4. Конфигурация

Переменные окружения:

| Переменная | Тип | По умолчанию | Описание |
|------------|-----|--------------|----------|
| `DATABASE_URL` | string | — | PostgreSQL connection string (обязательно) |
| `BOT_TOKEN` | string | — | Токен Telegram бота (обязательно) |
| `API_URL` | string | `http://api:8000` | URL API для бота |
| `API_HOST` | string | `0.0.0.0` | Хост для API |
| `API_PORT` | int | `8000` | Порт для API |
| `METRICS_PORT` | int | `8000` | Порт для метрик (тот же что API) |
| `NOTIFICATION_HOUR` | int | `10` | Час отправки уведомлений (0-23) |
| `LOG_LEVEL` | string | `INFO` | Уровень логирования |
| `LOG_FORMAT` | string | `json` | Формат логов: `json` или `console` |
| `THROTTLE_RATE` | int | `30` | Лимит сообщений в минуту |

```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str  # postgresql+asyncpg://user:pass@host:5432/db
    
    # Telegram Bot
    bot_token: str
    api_url: str = "http://api:8000"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Scheduler
    notification_hour: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Rate limiting
    throttle_rate: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 4.5. API Endpoints

#### Users

| Метод | Endpoint | Описание | Request Body | Response |
|-------|----------|----------|--------------|----------|
| `POST` | `/users` | Создать или обновить пользователя | `UserCreate` | `User` |
| `GET` | `/users/{telegram_id}` | Получить пользователя | — | `User` |

#### Subscriptions

| Метод | Endpoint | Описание | Request Body | Response |
|-------|----------|----------|--------------|----------|
| `GET` | `/users/{telegram_id}/subscriptions` | Список подписок | — | `list[Subscription]` |
| `POST` | `/users/{telegram_id}/subscriptions` | Создать подписку | `SubscriptionCreate` | `Subscription` |
| `GET` | `/subscriptions/{id}` | Получить подписку | — | `Subscription` |
| `PATCH` | `/subscriptions/{id}` | Обновить подписку | `SubscriptionUpdate` | `Subscription` |
| `DELETE` | `/subscriptions/{id}` | Удалить подписку (soft) | — | `{"ok": true}` |

#### Stats

| Метод | Endpoint | Описание | Response |
|-------|----------|----------|----------|
| `GET` | `/users/{telegram_id}/stats` | Статистика пользователя | `UserStats` |

#### System

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/health` | Healthcheck |
| `GET` | `/metrics` | Prometheus метрики |

### 4.6. Pydantic Schemas (API)

```python
# src/api/schemas.py
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

class Period(int, Enum):
    WEEKLY = 7
    MONTHLY = 30
    YEARLY = 365

# === Users ===

class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None

class User(BaseModel):
    telegram_id: int
    username: str | None
    first_name: str | None
    last_seen: datetime | None
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Subscriptions ===

class SubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    currency: Currency = Currency.RUB
    period_days: int = Field(..., gt=0, le=365)
    next_payment: date
    notify_days: int = Field(default=3, ge=0)
    
    @field_validator("next_payment")
    @classmethod
    def payment_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("next_payment cannot be in the past")
        return v
    
    @field_validator("notify_days")
    @classmethod  
    def notify_within_period(cls, v: int, info) -> int:
        period = info.data.get("period_days")
        if period and v > period:
            raise ValueError("notify_days cannot exceed period_days")
        return v

class SubscriptionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    amount: float | None = Field(None, gt=0)
    currency: Currency | None = None
    period_days: int | None = Field(None, gt=0, le=365)
    next_payment: date | None = None
    notify_days: int | None = Field(None, ge=0)

class Subscription(BaseModel):
    id: int
    telegram_id: int
    name: str
    amount: float
    currency: Currency
    period_days: int
    next_payment: date
    notify_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === Stats ===

class CurrencyStats(BaseModel):
    currency: Currency
    total_monthly: float
    count: int

class UpcomingPayment(BaseModel):
    subscription_id: int
    name: str
    amount: float
    currency: Currency
    date: date
    days_left: int

class UserStats(BaseModel):
    total_subscriptions: int
    total_monthly_rub: float
    by_currency: list[CurrencyStats]
    upcoming_payments: list[UpcomingPayment]
```

### 4.7. Repository (Database Layer)

```python
# src/db/repository.py
from datetime import date, datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Subscription

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def upsert(self, telegram_id: int, username: str | None, first_name: str | None) -> User:
        """Создать или обновить пользователя"""
        ...
    
    async def get(self, telegram_id: int) -> User | None:
        """Получить пользователя по telegram_id"""
        ...
    
    async def update_last_seen(self, telegram_id: int) -> None:
        """Обновить время последней активности"""
        ...
    
    async def count_active_24h(self) -> int:
        """Количество пользователей, активных за 24 часа"""
        ...


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, telegram_id: int, data: dict) -> Subscription:
        """Создать подписку"""
        ...
    
    async def get_by_id(self, subscription_id: int) -> Subscription | None:
        """Получить подписку по ID"""
        ...
    
    async def get_all_by_user(self, telegram_id: int) -> list[Subscription]:
        """Получить все активные подписки пользователя"""
        ...
    
    async def update(self, subscription_id: int, data: dict) -> Subscription | None:
        """Обновить подписку"""
        ...
    
    async def soft_delete(self, subscription_id: int) -> bool:
        """Пометить подписку как неактивную"""
        ...
    
    async def get_pending_notifications(self, target_date: date) -> list[Subscription]:
        """Получить подписки, требующие уведомления"""
        # WHERE next_payment - notify_days <= target_date AND is_active = true
        ...
    
    async def advance_next_payment(self, subscription_id: int) -> bool:
        """Сдвинуть next_payment на следующий период"""
        ...
    
    async def get_stats(self, telegram_id: int) -> dict:
        """Получить статистику для пользователя"""
        ...
```

### 4.8. Bot API Client

```python
# src/bot/api_client.py
import httpx
from src.core.config import settings

class APIClient:
    def __init__(self):
        self.base_url = settings.api_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
    
    async def create_user(self, telegram_id: int, username: str | None, first_name: str | None) -> dict:
        response = await self.client.post("/users", json={
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
        })
        response.raise_for_status()
        return response.json()
    
    async def get_subscriptions(self, telegram_id: int) -> list[dict]:
        response = await self.client.get(f"/users/{telegram_id}/subscriptions")
        response.raise_for_status()
        return response.json()
    
    async def create_subscription(self, telegram_id: int, data: dict) -> dict:
        response = await self.client.post(f"/users/{telegram_id}/subscriptions", json=data)
        response.raise_for_status()
        return response.json()
    
    async def update_subscription(self, subscription_id: int, data: dict) -> dict:
        response = await self.client.patch(f"/subscriptions/{subscription_id}", json=data)
        response.raise_for_status()
        return response.json()
    
    async def delete_subscription(self, subscription_id: int) -> bool:
        response = await self.client.delete(f"/subscriptions/{subscription_id}")
        response.raise_for_status()
        return True
    
    async def get_stats(self, telegram_id: int) -> dict:
        response = await self.client.get(f"/users/{telegram_id}/stats")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
```

### 4.9. FSM состояния для /add (без изменений)

```python
from aiogram.fsm.state import State, StatesGroup

class AddSubscription(StatesGroup):
    name = State()
    amount = State()
    currency = State()
    period = State()
    custom_period = State()
    next_payment = State()
    notify_days = State()
```

## 5. Деплой

### 5.1. Containerfile.api

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "src.api.main"]
```

### 5.2. Containerfile.bot

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN useradd -m -u 1000 botuser
USER botuser

# Бот не имеет HTTP endpoint, healthcheck через процесс
HEALTHCHECK --interval=30s --timeout=3s \
    CMD pgrep -f "python -m src.bot.main" || exit 1

CMD ["python", "-m", "src.bot.main"]
```

### 5.3. Compose для Podman

```yaml
version: "3"

services:
  # PostgreSQL
  postgres:
    image: docker.io/postgres:16-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-subscriptions}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-subscriptions}
      POSTGRES_DB: ${POSTGRES_DB:-subscriptions}
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-subscriptions}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI
  api:
    build:
      context: ..
      dockerfile: deploy/Containerfile.api
    container_name: subscription-api
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-subscriptions}:${POSTGRES_PASSWORD:-subscriptions}@postgres:5432/${POSTGRES_DB:-subscriptions}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      LOG_FORMAT: ${LOG_FORMAT:-json}
      NOTIFICATION_HOUR: ${NOTIFICATION_HOUR:-10}
      BOT_TOKEN: ${BOT_TOKEN}  # Нужен для отправки уведомлений
    ports:
      - "8000:8000"
    networks:
      - backend
      - monitoring

  # Telegram Bot
  bot:
    build:
      context: ..
      dockerfile: deploy/Containerfile.bot
    container_name: subscription-bot
    restart: unless-stopped
    depends_on:
      - api
    environment:
      BOT_TOKEN: ${BOT_TOKEN}
      API_URL: http://api:8000
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      LOG_FORMAT: ${LOG_FORMAT:-json}
      THROTTLE_RATE: ${THROTTLE_RATE:-30}
    networks:
      - backend

  # Prometheus
  prometheus:
    image: docker.io/prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro,Z
      - prometheus_data:/prometheus:Z
    ports:
      - "9090:9090"
    networks:
      - monitoring
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  # Grafana
  grafana:
    image: docker.io/grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    volumes:
      - grafana_data:/var/lib/grafana:Z
    ports:
      - "3000:3000"
    networks:
      - monitoring
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:

networks:
  backend:
    driver: bridge
  monitoring:
    driver: bridge
```

### 5.4. Prometheus конфиг

```yaml
# deploy/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'subscription-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
```

### 5.5. Alembic (миграции)

Инициализация:
```bash
alembic init alembic
```

Конфиг `alembic.ini`:
```ini
[alembic]
script_location = alembic
sqlalchemy.url = %(DATABASE_URL)s
```

Создание миграции:
```bash
alembic revision --autogenerate -m "Initial tables"
```

Применение миграций:
```bash
alembic upgrade head
```

В `compose.yml` миграции можно запускать автоматически при старте API:
```yaml
api:
  command: sh -c "alembic upgrade head && python -m src.api.main"
```

### 5.6. Интеграция с systemd через Podlet (Bluefin)

```bash
# Генерация systemd units из compose
cd deploy
podlet generate compose.yml

# Файлы будут созданы в ~/.config/containers/systemd/
# subscription-api.container
# subscription-bot.container
# postgres.container
# prometheus.container
# grafana.container

# Активация
systemctl --user daemon-reload
systemctl --user enable --now subscription-api subscription-bot postgres prometheus grafana
```

## 6. Тестирование

### 6.1. Unit-тесты

Минимальный набор тестов:
- `test_repository.py` — CRUD операции с БД
- `test_stats.py` — расчёт статистики
- `test_notifications.py` — логика определения подписок для уведомления

### 6.2. Запуск тестов

```bash
pytest tests/ -v --asyncio-mode=auto
```

## 7. Ограничения и допущения

1. **Часовой пояс** — используется часовой пояс сервера для уведомлений
2. **Курсы валют** — фиксированные (USD=90, EUR=100) или не конвертируются
3. **Один бот на пользователя** — нет поддержки нескольких аккаунтов
4. **Нет истории платежей** — только учёт будущих списаний
5. **Нет экспорта данных** — данные только внутри системы
6. **Нет группового использования** — бот работает только в личных сообщениях
7. **API без аутентификации** — предполагается работа только внутри docker-сети
8. **Нет rate limiting на API** — только на стороне бота

## 8. Возможные улучшения (не входят в MVP)

- [ ] Интеграция с API курсов валют
- [ ] Экспорт в CSV/PDF
- [ ] История платежей
- [ ] Категории подписок
- [ ] Напоминания в точное время пользователя (с учётом timezone)
- [ ] Интеграция с календарём (Google Calendar)
- [ ] Многоязычность (i18n)
- [ ] Web-интерфейс (отдельный фронтенд на React/Vue)
- [ ] Аутентификация API (JWT/API keys)
- [ ] API rate limiting
- [ ] Поддержка нескольких ботов/интерфейсов
- [ ] Импорт подписок из банковских выписок
