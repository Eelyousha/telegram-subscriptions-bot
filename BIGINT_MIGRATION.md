# Миграция telegram_id на BigInteger (int64)

## Статус: ✅ ЗАВЕРШЕНО

Дата: 2026-01-12

---

## Проблема

Telegram ID пользователей могут превышать значение `int32` (2,147,483,647), так как Telegram использует 64-битные идентификаторы. Использование обычного `Integer` в SQLAlchemy приводит к ограничению диапазона значений, что может вызвать ошибки при работе с пользователями с большими ID.

## Решение

Изменен тип колонки `telegram_id` с `Integer` (int32) на `BigInteger` (int64) в обеих таблицах:
- `users.telegram_id` (первичный ключ)
- `subscriptions.telegram_id` (внешний ключ)

---

## Изменения в коде

### Обновленный файл: [src/db/models.py](src/db/models.py)

**Было:**
```python
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String

class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(primary_key=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    telegram_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), index=True
    )
```

**Стало:**
```python
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)

class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), index=True
    )
```

---

## Миграция базы данных

### Создана миграция: [alembic/versions/002_bigint_telegram_id.py](alembic/versions/002_bigint_telegram_id.py)

**Revision ID:** `002`
**Revises:** `001`

### Применение миграции

Для применения миграции к существующей базе данных:

```bash
# Применить миграцию
poetry run alembic upgrade head

# Или через Docker
docker compose exec api alembic upgrade head
```

### Откат миграции (если необходимо)

⚠️ **Внимание:** Откат не сработает, если в базе есть telegram_id > 2,147,483,647

```bash
# Откатить последнюю миграцию
poetry run alembic downgrade -1

# Или через Docker
docker compose exec api alembic downgrade -1
```

---

## Технические детали

### Диапазоны значений:

| Тип | Диапазон | Использование |
|-----|----------|---------------|
| **Integer (int32)** | -2,147,483,648 до 2,147,483,647 | ❌ Недостаточно для Telegram ID |
| **BigInteger (int64)** | -9,223,372,036,854,775,808 до 9,223,372,036,854,775,807 | ✅ Достаточно для всех Telegram ID |

### Примеры Telegram ID:

```python
# Старые пользователи (2013-2015)
telegram_id = 12345678  # ✅ Работает с int32

# Современные пользователи (2020+)
telegram_id = 5678901234  # ❌ Превышает int32 (2,147,483,647)

# С BigInteger все работает
telegram_id = 9876543210  # ✅ Работает с int64
```

---

## Особенности миграции для разных СУБД

### PostgreSQL
```sql
-- Простое изменение типа
ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT;
ALTER TABLE subscriptions ALTER COLUMN telegram_id TYPE BIGINT;
```

### SQLite
SQLite не поддерживает `ALTER COLUMN`, поэтому миграция использует `batch_alter_table`:

```python
with op.batch_alter_table('users', schema=None) as batch_op:
    batch_op.alter_column('telegram_id',
                          existing_type=sa.Integer(),
                          type_=sa.BigInteger(),
                          existing_nullable=False)
```

Alembic автоматически:
1. Создает временную таблицу с новой схемой
2. Копирует данные
3. Удаляет старую таблицу
4. Переименовывает временную таблицу

---

## Тестирование

### Запуск тестов после миграции:

```bash
poetry run pytest tests/ -v
```

### Результаты:
```
============================= test session starts ==============================
collected 35 items

✅ 35 passed in 3.86s
```

Все существующие тесты прошли успешно, что подтверждает обратную совместимость изменений.

---

## Влияние на производительность

### Память:
- **Integer (int32):** 4 байта на значение
- **BigInteger (int64):** 8 байт на значение
- **Разница:** +4 байта на каждый telegram_id

### Для 100,000 пользователей:
- Дополнительно: ~400 KB (пренебрежимо мало)

### Индексы:
- Размер индексов увеличится на ~50%
- Скорость поиска остается O(log n)
- Практическое влияние: незначительное

### Вывод:
✅ Влияние на производительность минимальное и не критично для большинства приложений

---

## Обратная совместимость

### Python код:
✅ **Полностью совместим** - Python `int` поддерживает произвольную длину

```python
# Работает с обоими типами
telegram_id: int = 12345678  # int32
telegram_id: int = 9876543210  # int64

# В Pydantic моделях
class UserCreate(BaseModel):
    telegram_id: int  # ✅ Работает с любым значением
```

### API:
✅ **Полностью совместим** - JSON поддерживает произвольно большие числа

```json
{
  "telegram_id": 9876543210,
  "username": "user"
}
```

### Существующие данные:
✅ **Автоматически конвертируются** - все существующие int32 значения остаются валидными в int64

---

## Checklist для применения

- [x] Обновлены модели SQLAlchemy ([models.py](src/db/models.py))
- [x] Создана миграция Alembic ([002_bigint_telegram_id.py](alembic/versions/002_bigint_telegram_id.py))
- [x] Протестированы изменения (35/35 тестов)
- [x] Документация создана ([BIGINT_MIGRATION.md](BIGINT_MIGRATION.md))
- [ ] Миграция применена к development базе
- [ ] Миграция применена к production базе

---

## Команды для применения в production

```bash
# 1. Сделать бэкап базы данных
pg_dump -U user -d dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Применить миграцию
poetry run alembic upgrade head

# 3. Проверить успешность
poetry run alembic current

# 4. Проверить работу приложения
poetry run pytest tests/

# 5. Запустить API и бота
docker compose up -d
```

---

## Troubleshooting

### Ошибка: "integer out of range"
**Причина:** Старая база с int32
**Решение:** Применить миграцию `002`

### Ошибка при откате миграции
**Причина:** Есть значения > 2,147,483,647
**Решение:** Откат невозможен, нужно оставить BigInteger

### Alembic не видит миграцию
**Причина:** Кэш Python
**Решение:**
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
poetry run alembic upgrade head
```

---

## Рекомендации

1. ✅ **Применить миграцию как можно скорее** - предотвратит ошибки с новыми пользователями
2. ✅ **Протестировать на staging** перед production
3. ✅ **Сделать бэкап базы** перед миграцией в production
4. ✅ **Мониторить логи** после применения

---

## Заключение

Миграция на BigInteger является:
- ✅ **Необходимой** - предотвращает ошибки overflow
- ✅ **Безопасной** - все тесты пройдены
- ✅ **Обратно совместимой** - существующий код работает без изменений
- ✅ **Низкорисковой** - минимальное влияние на производительность

**Статус:** Готово к применению в production ✅

---

**Дата завершения:** 2026-01-12
**Версия миграции:** 002
**Тесты:** 35/35 ✅
