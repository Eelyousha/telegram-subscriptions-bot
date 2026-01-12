# Анализ качества кода: SOLID, DRY и паттерны проектирования

## Оглавление
1. [Анализ принципов SOLID](#анализ-принципов-solid)
2. [Анализ принципа DRY](#анализ-принципа-dry)
3. [Используемые паттерны проектирования](#используемые-паттерны-проектирования)
4. [Рекомендуемые улучшения](#рекомендуемые-улучшения)
5. [План внедрения](#план-внедрения)

---

## Анализ принципов SOLID

### ✅ S — Single Responsibility Principle (Принцип единственной ответственности)

**Статус**: **Хорошо соблюдается**

#### Положительные примеры:
- **Repositories** ([src/db/repository.py](src/db/repository.py)): Отвечают только за доступ к данным
- **API Routes** ([src/api/routes/](src/api/routes/)): Каждый роутер отвечает за свой домен (users, subscriptions, health)
- **Bot Handlers** ([src/bot/handlers/](src/bot/handlers/)): Каждый handler отвечает за одну команду
- **Config** ([src/core/config.py](src/core/config.py)): Только загрузка конфигурации
- **Logging** ([src/core/logging.py](src/core/logging.py)): Только настройка логирования

#### ⚠️ Нарушения:
1. **`get_user_stats()` в routes/subscriptions.py:84-147**
   - Проблема: Роут содержит бизнес-логику расчета статистики (93-147 строки)
   - Нарушает SRP: роут должен только обрабатывать HTTP, а не вычислять
   - Решение: Вынести логику в отдельный `SubscriptionService`

2. **`get_total_monthly_amount_rub()` в repository.py:190-213**
   - Проблема: Репозиторий содержит бизнес-логику конвертации периодов в месячные суммы
   - Дублирование: Та же логика есть в `get_user_stats()` (103-108)
   - Решение: Вынести в отдельный `CurrencyCalculator` или `SubscriptionService`

3. **`advance_past_payments()` в repository.py:161-182**
   - Проблема: Репозиторий содержит бизнес-логику продвижения дат
   - Решение: Переместить в `SubscriptionService`

---

### ❌ O — Open/Closed Principle (Принцип открытости/закрытости)

**Статус**: **Требует улучшения**

#### Проблемы:

1. **Жестко закодированные периоды и валюты**

   В [src/bot/handlers/add.py:78](src/bot/handlers/add.py#L78):
   ```python
   period_text = {"7": "неделя", "30": "месяц", "365": "год"}[period_data]
   ```

   - Проблема: Добавление нового периода требует изменения кода в нескольких местах
   - Дублирование: Та же логика в строке 170
   - Решение: Создать `PeriodMapper` класс

2. **Конвертация валют в нескольких местах**

   Формулы конвертации дублируются в:
   - [src/api/routes/subscriptions.py:103-108](src/api/routes/subscriptions.py#L103-L108)
   - [src/db/repository.py:204-210](src/db/repository.py#L204-L210)

   - Проблема: Изменение логики конвертации требует правки в двух местах
   - Решение: Создать `CurrencyConverter` с методом `to_monthly(amount, period_days)`

3. **Валидация разбросана по handlers**

   Каждый handler валидирует свои входные данные по-своему:
   - [add.py:28-30](src/bot/handlers/add.py#L28-L30) - валидация названия
   - [add.py:40-46](src/bot/handlers/add.py#L40-L46) - валидация суммы
   - [add.py:94-100](src/bot/handlers/add.py#L94-L100) - валидация периода

   - Решение: Использовать Pydantic модели для валидации на уровне бота

#### Рекомендации:

**Использовать Strategy Pattern для конвертации валют:**

```python
class PeriodConverter(ABC):
    @abstractmethod
    def to_monthly(self, amount: float, period_days: int) -> float:
        pass

class SimplePeriodConverter(PeriodConverter):
    def to_monthly(self, amount: float, period_days: int) -> float:
        if period_days == 7:
            return amount * 4.33
        elif period_days == 365:
            return amount / 12
        else:
            return amount * (30 / period_days)
```

---

### ⚠️ L — Liskov Substitution Principle (Принцип подстановки Барбары Лисков)

**Статус**: **Не применимо / Соблюдается**

- В проекте почти нет наследования (только базовые классы ORM)
- SQLAlchemy модели корректно наследуются от `Base`
- Нет нарушений LSP

---

### ❌ I — Interface Segregation Principle (Принцип разделения интерфейса)

**Статус**: **Требует улучшения**

#### Проблемы:

1. **Толстый APIClient** ([src/bot/api_client.py](src/bot/api_client.py))

   Клиент содержит методы для всех эндпоинтов:
   - `create_user()`, `get_user()`
   - `create_subscription()`, `get_subscriptions()`, `update_subscription()`, `delete_subscription()`, `get_user_stats()`

   - Проблема: Handlers зависят от всего клиента, хотя используют 1-2 метода
   - Решение: Разделить на `UserAPIClient` и `SubscriptionAPIClient`

2. **Репозитории смешивают CRUD и аналитику**

   `SubscriptionRepository`:
   - CRUD: `create()`, `get_by_id()`, `update()`, `soft_delete()`
   - Аналитика: `count_total()`, `get_total_monthly_amount_rub()`
   - Бизнес-логика: `get_pending_notifications()`, `advance_past_payments()`

   - Решение: Разделить на `SubscriptionRepository` (CRUD) и `SubscriptionAnalytics` (статистика)

#### Рекомендации:

**Разделить API клиент:**

```python
class BaseAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

class UserAPIClient(BaseAPIClient):
    async def create_user(self, ...): ...
    async def get_user(self, ...): ...

class SubscriptionAPIClient(BaseAPIClient):
    async def create_subscription(self, ...): ...
    async def get_subscriptions(self, ...): ...
    async def get_user_stats(self, ...): ...
```

---

### ✅ D — Dependency Inversion Principle (Принцип инверсии зависимостей)

**Статус**: **Частично соблюдается**

#### Положительные примеры:

1. **FastAPI Dependency Injection** ([src/api/dependencies.py](src/api/dependencies.py))
   ```python
   async def get_db() -> AsyncGenerator[AsyncSession, None]:
       async with AsyncSessionLocal() as session:
           yield session
   ```
   - Роуты зависят от абстракции (`AsyncSession`), а не от конкретной реализации

2. **Aiogram DI** ([src/bot/main.py](src/bot/main.py))
   ```python
   await dp.start_polling(bot, api_client=api_client)
   ```
   - Handlers получают `APIClient` через DI

#### ⚠️ Проблемы:

1. **Прямое создание репозиториев в роутах**

   [src/api/routes/subscriptions.py:21](src/api/routes/subscriptions.py#L21):
   ```python
   repo = SubscriptionRepository(session)
   ```

   - Проблема: Роут зависит от конкретной реализации `SubscriptionRepository`
   - Решение: Использовать `Depends(get_subscription_repository)`

2. **Глобальный синглтон Settings** ([src/core/config.py:36](src/core/config.py#L36))
   ```python
   settings = Settings()  # Глобальная переменная
   ```

   - Проблема: Все модули импортируют глобальный `settings`, сложно тестировать
   - Решение: Передавать через DI или использовать `Depends(get_settings)`

3. **Жестко закодированный APIClient**

   Bot handlers зависят от конкретного `APIClient`, нет интерфейса:
   - Сложно подменить для тестирования
   - Решение: Создать `Protocol` или `ABC` для API клиента

#### Рекомендации:

**Использовать Dependency Injection для репозиториев:**

```python
# src/api/dependencies.py
async def get_subscription_repository(
    session: AsyncSession = Depends(get_db)
) -> SubscriptionRepository:
    return SubscriptionRepository(session)

# src/api/routes/subscriptions.py
async def get_user_subscriptions(
    telegram_id: int,
    repo: SubscriptionRepository = Depends(get_subscription_repository),
) -> list[schemas.Subscription]:
    subscriptions = await repo.get_all_by_user(telegram_id)
    return [schemas.Subscription.model_validate(sub) for sub in subscriptions]
```

**Создать Protocol для API клиента:**

```python
from typing import Protocol

class IAPIClient(Protocol):
    async def create_subscription(self, telegram_id: int, data: dict) -> dict: ...
    async def get_subscriptions(self, telegram_id: int) -> list[dict]: ...
```

---

## Анализ принципа DRY (Don't Repeat Yourself)

### ❌ Нарушения DRY

#### 1. **Дублирование логики конвертации периодов в месячные**

**Локации:**
- [src/api/routes/subscriptions.py:103-108](src/api/routes/subscriptions.py#L103-L108)
- [src/db/repository.py:204-210](src/db/repository.py#L204-L210)

**Код дублируется 2 раза:**
```python
# routes/subscriptions.py
if sub.period_days == 7:
    monthly = sub.amount * 4.33
elif sub.period_days == 365:
    monthly = sub.amount / 12
else:
    monthly = sub.amount * (30 / sub.period_days)

# repository.py
if sub.period_days == 7:
    monthly = sub.amount * 4.33
elif sub.period_days == 365:
    monthly = sub.amount / 12
else:
    monthly = sub.amount * (30 / sub.period_days)
```

**Решение:**
```python
# src/services/currency.py
class CurrencyCalculator:
    @staticmethod
    def to_monthly_equivalent(amount: float, period_days: int) -> float:
        """Convert amount to monthly equivalent."""
        if period_days == 7:
            return amount * 4.33
        elif period_days == 365:
            return amount / 12
        else:
            return amount * (30 / period_days)
```

#### 2. **Дублирование маппинга периодов на текст**

**Локации:**
- [src/bot/handlers/add.py:78](src/bot/handlers/add.py#L78)
- [src/bot/handlers/add.py:170-172](src/bot/handlers/add.py#L170-L172)

**Код дублируется:**
```python
# Первое использование
period_text = {"7": "неделя", "30": "месяц", "365": "год"}[period_data]

# Второе использование
period_text = {7: "неделю", 30: "месяц", 365: "год"}.get(
    data["period_days"], f"{data['period_days']} дн."
)
```

**Решение:**
```python
# src/bot/formatters.py
class PeriodFormatter:
    PERIOD_NAMES = {
        7: "неделя",
        30: "месяц",
        365: "год"
    }

    @classmethod
    def format(cls, period_days: int, case: str = "nominative") -> str:
        """Format period days to human readable text."""
        cases = {
            "nominative": {7: "неделя", 30: "месяц", 365: "год"},
            "accusative": {7: "неделю", 30: "месяц", 365: "год"},
        }
        return cases[case].get(period_days, f"{period_days} дн.")
```

#### 3. **Дублирование логики обновления `updated_at`**

**Локации:**
- [src/db/repository.py:119](src/db/repository.py#L119) - в `update()`
- [src/db/repository.py:131](src/db/repository.py#L131) - в `soft_delete()`
- [src/db/repository.py:157](src/db/repository.py#L157) - в `advance_next_payment()`
- [src/db/repository.py:178](src/db/repository.py#L178) - в `advance_past_payments()`

**Решение:**
```python
# src/db/models.py - использовать SQLAlchemy onupdate
updated_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow,  # Автоматически обновляется
)
```

#### 4. **Дублирование сообщений об ошибках**

**Локации:**
- [src/api/routes/subscriptions.py:50](src/api/routes/subscriptions.py#L50): `"Subscription not found"`
- [src/api/routes/subscriptions.py:67](src/api/routes/subscriptions.py#L67): `"Subscription not found"`
- [src/api/routes/subscriptions.py:80](src/api/routes/subscriptions.py#L80): `"Subscription not found"`

**Решение:**
```python
# src/api/exceptions.py
class ErrorMessages:
    SUBSCRIPTION_NOT_FOUND = "Subscription not found"
    USER_NOT_FOUND = "User not found"
    INVALID_DATE = "Invalid date format"

# Использование
raise NotFoundException(ErrorMessages.SUBSCRIPTION_NOT_FOUND)
```

#### 5. **Дублирование паттерна "get or 404"**

**Локации:**
- [src/api/routes/subscriptions.py:47-51](src/api/routes/subscriptions.py#L47-L51)
- [src/api/routes/subscriptions.py:62-68](src/api/routes/subscriptions.py#L62-L68)
- [src/api/routes/subscriptions.py:77-81](src/api/routes/subscriptions.py#L77-L81)

**Решение:**
```python
# src/db/repository.py
async def get_by_id_or_raise(self, subscription_id: int) -> Subscription:
    """Get subscription by ID or raise NotFoundException."""
    subscription = await self.get_by_id(subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found")
    return subscription
```

#### 6. **Повторяющаяся валидация в handlers**

**Проблема:** Каждый handler бота вручную валидирует входные данные

**Решение:** Использовать Pydantic для валидации:
```python
# src/bot/schemas.py
from pydantic import BaseModel, Field, field_validator

class SubscriptionInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    period_days: int = Field(ge=1, le=365)
    notify_days: int = Field(ge=0)

    @field_validator('notify_days')
    def validate_notify_days(cls, v, values):
        if 'period_days' in values.data and v > values.data['period_days']:
            raise ValueError('Notify days cannot exceed period')
        return v
```

---

## Используемые паттерны проектирования

### ✅ Уже используются

#### 1. **Repository Pattern**
- [src/db/repository.py](src/db/repository.py)
- Инкапсулирует доступ к данным

#### 2. **Data Transfer Object (DTO)**
- [src/api/schemas.py](src/api/schemas.py)
- Pydantic модели для валидации API

#### 3. **Dependency Injection**
- FastAPI: [src/api/dependencies.py](src/api/dependencies.py)
- Aiogram: через `start_polling()` параметры

#### 4. **Middleware Pattern**
- [src/bot/middlewares.py](src/bot/middlewares.py)
- Logging, Throttling, Metrics

#### 5. **Router Pattern** (Module Pattern)
- API: [src/api/routes/](src/api/routes/)
- Bot: [src/bot/handlers/](src/bot/handlers/)

#### 6. **Finite State Machine (FSM)**
- [src/bot/states.py](src/bot/states.py)
- Для многошаговых диалогов

#### 7. **Factory Pattern** (частично)
- `async_sessionmaker` для создания сессий БД
- Можно улучшить для репозиториев

#### 8. **Singleton Pattern**
- [src/core/config.py:36](src/core/config.py#L36) - `settings = Settings()`

---

## Рекомендуемые улучшения

### 1. **Service Layer Pattern** (ВЫСОКИЙ ПРИОРИТЕТ)

**Зачем:** Отделить бизнес-логику от HTTP/DB слоев

**Создать:**
```python
# src/services/subscription_service.py
from datetime import date
from src.db.repository import SubscriptionRepository
from src.services.currency import CurrencyCalculator

class SubscriptionService:
    def __init__(self, repo: SubscriptionRepository):
        self.repo = repo
        self.calculator = CurrencyCalculator()

    async def calculate_user_stats(self, telegram_id: int) -> dict:
        """Calculate comprehensive user statistics."""
        subscriptions = await self.repo.get_all_by_user(telegram_id)

        # Business logic here...
        currency_stats = {}
        for sub in subscriptions:
            monthly = self.calculator.to_monthly_equivalent(
                sub.amount, sub.period_days
            )
            # ...

        return {
            "total_subscriptions": len(subscriptions),
            "by_currency": currency_stats,
            "upcoming_payments": self._get_upcoming(subscriptions),
        }

    def _get_upcoming(self, subscriptions: list) -> list:
        """Get upcoming payments in next 30 days."""
        today = date.today()
        upcoming = [
            sub for sub in subscriptions
            if (sub.next_payment - today).days <= 30
        ]
        return sorted(upcoming, key=lambda x: x.next_payment)[:5]
```

**Использование в роуте:**
```python
# src/api/routes/subscriptions.py
@router.get("/users/{telegram_id}/stats")
async def get_user_stats(
    telegram_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
) -> schemas.UserStats:
    stats = await service.calculate_user_stats(telegram_id)
    return schemas.UserStats(**stats)
```

**Преимущества:**
- ✅ Соблюдение SRP
- ✅ Легко тестировать бизнес-логику
- ✅ Переиспользование логики между API и ботом
- ✅ Упрощение роутов

---

### 2. **Strategy Pattern для конвертации валют** (СРЕДНИЙ ПРИОРИТЕТ)

**Зачем:** Легко добавлять новые стратегии конвертации (реальные курсы валют)

```python
# src/services/currency.py
from abc import ABC, abstractmethod
from enum import Enum

class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

class PeriodConverter(ABC):
    """Abstract strategy for period conversion."""

    @abstractmethod
    def to_monthly(self, amount: float, period_days: int) -> float:
        pass

class SimplePeriodConverter(PeriodConverter):
    """Simple mathematical conversion."""

    def to_monthly(self, amount: float, period_days: int) -> float:
        if period_days == 7:
            return amount * 4.33
        elif period_days == 365:
            return amount / 12
        else:
            return amount * (30 / period_days)

class CurrencyConverter(ABC):
    """Abstract strategy for currency conversion."""

    @abstractmethod
    async def to_rub(self, amount: float, currency: Currency) -> float:
        pass

class StaticCurrencyConverter(CurrencyConverter):
    """Static exchange rates."""

    RATES = {
        Currency.RUB: 1.0,
        Currency.USD: 90.0,
        Currency.EUR: 100.0,
    }

    async def to_rub(self, amount: float, currency: Currency) -> float:
        return amount * self.RATES[currency]

class LiveCurrencyConverter(CurrencyConverter):
    """Fetch live rates from external API."""

    async def to_rub(self, amount: float, currency: Currency) -> float:
        # Fetch from external API
        rate = await self._fetch_rate(currency)
        return amount * rate

    async def _fetch_rate(self, currency: Currency) -> float:
        # API call implementation
        pass
```

**Использование:**
```python
# src/services/subscription_service.py
class SubscriptionService:
    def __init__(
        self,
        repo: SubscriptionRepository,
        period_converter: PeriodConverter,
        currency_converter: CurrencyConverter,
    ):
        self.repo = repo
        self.period_converter = period_converter
        self.currency_converter = currency_converter
```

---

### 3. **Unit of Work Pattern** (СРЕДНИЙ ПРИОРИТЕТ)

**Зачем:** Управление транзакциями, когда нужно работать с несколькими репозиториями

```python
# src/db/unit_of_work.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.repository import UserRepository, SubscriptionRepository

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.subscriptions = SubscriptionRepository(session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

# Использование
async with UnitOfWork(session) as uow:
    user = await uow.users.get(telegram_id)
    subscription = await uow.subscriptions.create(...)
    await uow.commit()
```

---

### 4. **Builder Pattern для создания уведомлений** (НИЗКИЙ ПРИОРИТЕТ)

**Зачем:** Гибкое создание сложных уведомлений

```python
# src/services/notification_builder.py
class NotificationBuilder:
    def __init__(self):
        self._text = ""
        self._keyboard = None

    def add_header(self, text: str) -> "NotificationBuilder":
        self._text += f"🔔 {text}\n\n"
        return self

    def add_subscription(self, name: str, amount: float, currency: str) -> "NotificationBuilder":
        self._text += f"{name} — {amount} {currency}\n"
        return self

    def add_date(self, date_str: str) -> "NotificationBuilder":
        self._text += f"📅 Дата: {date_str}\n"
        return self

    def with_keyboard(self, keyboard) -> "NotificationBuilder":
        self._keyboard = keyboard
        return self

    def build(self) -> tuple[str, Any]:
        return self._text, self._keyboard

# Использование
notification = (
    NotificationBuilder()
    .add_header("Скоро списание")
    .add_subscription("Netflix", 500, "RUB")
    .add_date("15.01.2026")
    .with_keyboard(get_keyboard())
    .build()
)
```

---

### 5. **Observer Pattern для метрик** (НИЗКИЙ ПРИОРИТЕТ)

**Зачем:** Автоматическое обновление метрик при изменении данных

```python
# src/services/events.py
from typing import Callable, List

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, List[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    async def publish(self, event: str, **kwargs):
        if event in self._subscribers:
            for callback in self._subscribers[event]:
                await callback(**kwargs)

# Использование
event_bus = EventBus()

event_bus.subscribe("subscription_created", update_metrics)
event_bus.subscribe("subscription_deleted", update_metrics)

# В репозитории
async def create(self, ...):
    subscription = Subscription(...)
    await self.session.commit()
    await event_bus.publish("subscription_created", subscription=subscription)
```

---

### 6. **Decorator Pattern для валидации** (СРЕДНИЙ ПРИОРИТЕТ)

**Зачем:** Переиспользуемая валидация для handlers

```python
# src/bot/decorators.py
from functools import wraps

def validate_subscription_owner(func):
    """Ensure user owns the subscription before modification."""
    @wraps(func)
    async def wrapper(callback: CallbackQuery, api_client: APIClient, **kwargs):
        subscription_id = int(callback.data.split(":")[1])
        subscription = await api_client.get_subscription(subscription_id)

        if subscription["telegram_id"] != callback.from_user.id:
            await callback.answer("❌ Это не ваша подписка", show_alert=True)
            return

        return await func(callback, api_client, **kwargs)
    return wrapper

# Использование
@router.callback_query(F.data.startswith("delete:"))
@validate_subscription_owner
async def confirm_delete(callback: CallbackQuery, api_client: APIClient):
    # Handler logic...
    pass
```

---

### 7. **Facade Pattern для упрощения API клиента** (НИЗКИЙ ПРИОРИТЕТ)

**Зачем:** Упростить сложные операции для bot handlers

```python
# src/bot/api_facade.py
class APIFacade:
    def __init__(self, client: APIClient):
        self.client = client

    async def create_subscription_with_user(
        self,
        telegram_id: int,
        username: str,
        subscription_data: dict,
    ) -> dict:
        """Create user if not exists, then create subscription."""
        await self.client.create_user(telegram_id, username)
        subscription = await self.client.create_subscription(
            telegram_id, subscription_data
        )
        return subscription

    async def get_full_user_data(self, telegram_id: int) -> dict:
        """Get user with subscriptions and stats."""
        user = await self.client.get_user(telegram_id)
        subscriptions = await self.client.get_subscriptions(telegram_id)
        stats = await self.client.get_user_stats(telegram_id)

        return {
            "user": user,
            "subscriptions": subscriptions,
            "stats": stats,
        }
```

---

## План внедрения

### Фаза 1: Рефакторинг дублирования кода (1-2 дня)

**Приоритет:** КРИТИЧЕСКИЙ

1. ✅ Создать `CurrencyCalculator` с методом `to_monthly_equivalent()`
2. ✅ Создать `PeriodFormatter` для текстового представления
3. ✅ Добавить `onupdate=datetime.utcnow` в модель для автоматического `updated_at`
4. ✅ Создать `ErrorMessages` константы
5. ✅ Добавить `get_by_id_or_raise()` в репозиторий

**Результат:** Устранение всех нарушений DRY

---

### Фаза 2: Внедрение Service Layer (2-3 дня)

**Приоритет:** ВЫСОКИЙ

1. ✅ Создать `src/services/` директорию
2. ✅ Создать `SubscriptionService` с методами:
   - `calculate_user_stats()`
   - `create_subscription()`
   - `update_subscription()`
3. ✅ Создать `UserService`
4. ✅ Обновить роуты для использования сервисов через DI
5. ✅ Переместить бизнес-логику из репозиториев в сервисы

**Результат:** Соблюдение SRP, улучшение тестируемости

---

### Фаза 3: Разделение интерфейсов (1-2 дня)

**Приоритет:** СРЕДНИЙ

1. ✅ Разделить `APIClient` на `UserAPIClient` и `SubscriptionAPIClient`
2. ✅ Создать `Protocol` или `ABC` для API клиентов
3. ✅ Разделить `SubscriptionRepository` на:
   - `SubscriptionRepository` (CRUD)
   - `SubscriptionAnalytics` (метрики)

**Результат:** Соблюдение ISP

---

### Фаза 4: Strategy Pattern для конвертации (1 день)

**Приоритет:** СРЕДНИЙ

1. ✅ Создать `PeriodConverter` стратегии
2. ✅ Создать `CurrencyConverter` с `StaticCurrencyConverter`
3. ✅ Опционально: `LiveCurrencyConverter` с внешним API

**Результат:** Соблюдение OCP, легкость расширения

---

### Фаза 5: Улучшение DI (1 день)

**Приоритет:** СРЕДНИЙ

1. ✅ Создать `get_subscription_service()` dependency
2. ✅ Создать `get_settings()` dependency вместо глобального синглтона
3. ✅ Использовать `Depends()` для всех репозиториев в роутах

**Результат:** Полное соблюдение DIP, улучшение тестируемости

---

### Фаза 6: Дополнительные паттерны (опционально, 2-3 дня)

**Приоритет:** НИЗКИЙ

1. ⚠️ Unit of Work Pattern
2. ⚠️ Builder Pattern для уведомлений
3. ⚠️ Observer Pattern для метрик
4. ⚠️ Decorator Pattern для валидации

**Результат:** Дополнительное улучшение архитектуры

---

## Метрики улучшения

### До рефакторинга:
- ❌ Дублирование кода: **6 мест**
- ❌ Нарушений SRP: **3**
- ❌ Нарушений OCP: **3 категории**
- ❌ Нарушений ISP: **2**
- ⚠️ Частичное DIP

### После рефакторинга (Фазы 1-5):
- ✅ Дублирование кода: **0**
- ✅ Нарушений SRP: **0**
- ✅ Нарушений OCP: **0**
- ✅ Нарушений ISP: **0**
- ✅ Полное соблюдение DIP

### Оценка времени:
- **Фазы 1-3 (критические):** 4-7 дней
- **Фазы 4-5 (важные):** 2 дня
- **Фаза 6 (опциональная):** 2-3 дня
- **Итого:** 6-12 дней для полного рефакторинга

---

## Заключение

Кодовая база проекта имеет **хорошую архитектурную основу**, но есть возможности для улучшения:

### Сильные стороны:
✅ Чистое разделение на микросервисы (API + Bot)
✅ Использование Repository Pattern
✅ Async-first подход
✅ Dependency Injection (FastAPI)
✅ Хорошая наблюдаемость (логи, метрики)

### Точки роста:
⚠️ Дублирование бизнес-логики
⚠️ Смешивание ответственностей (роуты + бизнес-логика)
⚠️ Отсутствие Service Layer
⚠️ Жесткая связанность компонентов

### Рекомендация:
Начать с **Фаз 1-3** (критический приоритет) для устранения технического долга и улучшения поддерживаемости кода. Это даст максимальную отдачу при минимальных затратах времени.
