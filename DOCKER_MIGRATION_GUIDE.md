# Пошаговая инструкция: Миграция на BigInteger в Docker Compose

## 🎯 Быстрый старт (Рекомендуемый способ)

### Для работающего приложения:

```bash
# Шаг 1: Бэкап базы данных
docker compose exec db pg_dump -U subscriptions_user subscriptions > backup_before_migration.sql

# Шаг 2: Применить миграцию
docker compose exec api alembic upgrade head

# Шаг 3: Проверить
docker compose exec api alembic current

# Шаг 4: Перезапустить сервисы
docker compose restart api bot

# Готово! ✅
```

---

## 📋 Детальная инструкция

### Шаг 1: Подготовка

#### 1.1 Проверьте статус контейнеров

```bash
docker compose ps
```

Ожидаемый вывод:
```
NAME                                  COMMAND                  SERVICE   STATUS          PORTS
telegram-subscriptions-bot-api-1      "python -m src.api.m…"   api       Up 10 minutes   0.0.0.0:8000->8000/tcp
telegram-subscriptions-bot-bot-1      "python -m src.bot.m…"   bot       Up 10 minutes
telegram-subscriptions-bot-db-1       "docker-entrypoint.s…"   db        Up 10 minutes   5432/tcp
```

Если контейнеры не запущены:
```bash
docker compose up -d
```

#### 1.2 Проверьте текущую версию миграции

```bash
docker compose exec api alembic current
```

Должно показать:
```
001 (head)
```

---

### Шаг 2: Создание бэкапа (ОБЯЗАТЕЛЬНО!)

#### Вариант A: Быстрый бэкап (рекомендуется)

```bash
docker compose exec db pg_dump -U subscriptions_user subscriptions > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Вариант B: Бэкап с компрессией

```bash
docker compose exec db pg_dump -U subscriptions_user subscriptions | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Вариант C: Бэкап через volume

```bash
docker run --rm \
  -v telegram-subscriptions-bot_postgres_data:/data \
  -v $(pwd):/backup \
  postgres:16-alpine \
  tar czf /backup/postgres_volume_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

#### Проверка бэкапа

```bash
# Проверить размер файла
ls -lh backup_*.sql

# Проверить содержимое (первые строки)
head -n 20 backup_*.sql
```

Если файл пустой или очень маленький (<1KB) - бэкап не удался, не продолжайте!

---

### Шаг 3: Применение миграции

#### 3.1 Применить миграцию

```bash
docker compose exec api alembic upgrade head
```

Ожидаемый вывод:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Change telegram_id to BigInteger
```

#### 3.2 Проверить применение

```bash
docker compose exec api alembic current
```

Должно показать:
```
002 (head)
```

#### 3.3 Проверить историю миграций

```bash
docker compose exec api alembic history
```

Ожидаемый вывод:
```
001 -> 002 (head), Change telegram_id to BigInteger
<base> -> 001, Initial schema
```

---

### Шаг 4: Проверка базы данных

#### 4.1 Проверить тип колонки в PostgreSQL

```bash
docker compose exec db psql -U subscriptions_user -d subscriptions -c "\d users"
```

Ожидаемый вывод:
```
                           Table "public.users"
   Column    |            Type             | Collation | Nullable | Default
-------------+-----------------------------+-----------+----------+---------
 telegram_id | bigint                      |           | not null |         <-- Должно быть bigint!
 username    | character varying(255)      |           |          |
 first_name  | character varying(255)      |           |          |
 ...
```

#### 4.2 Проверить внешние ключи

```bash
docker compose exec db psql -U subscriptions_user -d subscriptions -c "\d subscriptions"
```

Убедитесь, что `telegram_id` также `bigint`.

---

### Шаг 5: Перезапуск сервисов

#### 5.1 Перезапустить API и бота

```bash
docker compose restart api bot
```

#### 5.2 Проверить логи

```bash
docker compose logs -f api bot
```

Ищите успешный старт:
```
api-1  | INFO:     Application startup complete.
bot-1  | INFO     bot_started
```

Нажмите `Ctrl+C` для выхода из логов.

---

### Шаг 6: Функциональное тестирование

#### 6.1 Проверить API health check

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{"status":"healthy"}
```

#### 6.2 Проверить работу с большими telegram_id

Создайте тестового пользователя через Telegram бота или API:

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 9876543210,
    "username": "testuser",
    "first_name": "Test"
  }'
```

Если получили успешный ответ - миграция прошла успешно! ✅

#### 6.3 Проверить существующие данные

```bash
docker compose exec db psql -U subscriptions_user -d subscriptions -c "SELECT telegram_id, username FROM users LIMIT 5;"
```

Все существующие пользователи должны быть на месте.

---

## 🔄 План отката (Rollback)

### ⚠️ ВНИМАНИЕ
Откат возможен **ТОЛЬКО** если в базе нет telegram_id > 2,147,483,647!

### Команды для отката

```bash
# 1. Остановить сервисы
docker compose stop api bot

# 2. Откатить миграцию
docker compose exec api alembic downgrade -1

# 3. Проверить версию
docker compose exec api alembic current
# Должно показать: 001 (head)

# 4. Восстановить из бэкапа (если что-то пошло не так)
docker compose exec -T db psql -U subscriptions_user -d subscriptions < backup_before_migration.sql

# 5. Перезапустить сервисы
docker compose start api bot
```

---

## 🚀 Автоматизация (CI/CD)

### Создание init-контейнера для миграций

Добавьте в `docker-compose.yml`:

```yaml
services:
  # Existing services...

  migrate:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql+asyncpg://subscriptions_user:subscriptions_pass@db:5432/subscriptions
    command: alembic upgrade head
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    restart: "no"
```

### Использование в deploy-скрипте

```bash
#!/bin/bash
set -e

echo "🔄 Pulling latest changes..."
git pull

echo "🏗️  Building images..."
docker compose build

echo "💾 Creating backup..."
docker compose exec db pg_dump -U subscriptions_user subscriptions > backup_$(date +%Y%m%d_%H%M%S).sql

echo "🔄 Running migrations..."
docker compose up migrate

echo "♻️  Restarting services..."
docker compose restart api bot

echo "✅ Deployment complete!"
docker compose ps
```

Сохраните как `deploy.sh` и запускайте:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📊 Мониторинг миграции

### Во время миграции

Откройте второй терминал и следите за логами:

```bash
# Терминал 1: Применить миграцию
docker compose exec api alembic upgrade head

# Терминал 2: Следить за логами БД
docker compose logs -f db
```

### Проверка производительности

```bash
# Размер таблиц до и после
docker compose exec db psql -U subscriptions_user -d subscriptions -c "
SELECT
  table_name,
  pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
"
```

### Проверка индексов

```bash
docker compose exec db psql -U subscriptions_user -d subscriptions -c "
SELECT
  indexname,
  tablename,
  pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
"
```

---

## ❌ Типичные ошибки и решения

### Ошибка: "Permission denied"

```bash
# Решение: запустите с правами администратора
sudo docker compose exec api alembic upgrade head
```

### Ошибка: "No such service: api"

```bash
# Проверьте имена сервисов
docker compose ps

# Используйте правильное имя
docker compose exec <имя-сервиса> alembic upgrade head
```

### Ошибка: "Can't locate revision identified by '001'"

```bash
# Alembic не видит файлы миграций, пересоберите образ
docker compose build api
docker compose up -d api
docker compose exec api alembic upgrade head
```

### Ошибка: Database connection failed

```bash
# Проверьте статус БД
docker compose ps db

# Проверьте логи БД
docker compose logs db

# Перезапустите БД
docker compose restart db
sleep 5
docker compose exec api alembic upgrade head
```

### База данных заблокирована

```bash
# Проверьте активные подключения
docker compose exec db psql -U subscriptions_user -d subscriptions -c "
SELECT pid, usename, application_name, state
FROM pg_stat_activity
WHERE datname = 'subscriptions';
"

# Завершите висящие подключения (осторожно!)
docker compose exec db psql -U subscriptions_user -d subscriptions -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'subscriptions' AND pid != pg_backend_pid();
"
```

---

## ✅ Checklist для Production

- [ ] Создан бэкап базы данных
- [ ] Бэкап проверен (размер > 0)
- [ ] Сервисы работают до миграции
- [ ] Миграция протестирована на staging/dev
- [ ] Определено окно обслуживания (downtime)
- [ ] Команда уведомлена о миграции
- [ ] План отката подготовлен
- [ ] Миграция применена: `docker compose exec api alembic upgrade head`
- [ ] Версия проверена: `docker compose exec api alembic current` -> 002
- [ ] Сервисы перезапущены: `docker compose restart api bot`
- [ ] Логи проверены: `docker compose logs api bot`
- [ ] Функциональность протестирована
- [ ] Мониторинг в норме
- [ ] Бэкап сохранен в безопасном месте

---

## 📞 Поддержка

Если возникли проблемы:

1. **Не паникуйте!** - бэкап создан
2. **Проверьте логи**: `docker compose logs api bot db`
3. **Откатите миграцию**: `docker compose exec api alembic downgrade -1`
4. **Восстановите бэкап**: `docker compose exec -T db psql -U subscriptions_user -d subscriptions < backup.sql`
5. **Создайте issue** с описанием проблемы и логами

---

## 🎓 Дополнительные команды

### Просмотр всех миграций

```bash
docker compose exec api alembic history --verbose
```

### Проверка pending миграций

```bash
docker compose exec api alembic heads
docker compose exec api alembic current
```

### Dry-run миграции (проверка SQL)

```bash
docker compose exec api alembic upgrade head --sql
```

### Просмотр структуры всех таблиц

```bash
docker compose exec db psql -U subscriptions_user -d subscriptions -c "\dt+"
```

---

**Готово!** 🎉

Ваша база данных теперь поддерживает Telegram ID в формате int64!
