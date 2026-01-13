#!/bin/bash

# Скрипт для безопасной миграции базы данных в Docker Compose
# Использование: ./scripts/migrate.sh

set -e  # Остановить при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка наличия docker compose
if ! command -v docker compose &> /dev/null; then
    error "docker compose не найден. Установите Docker Compose."
    exit 1
fi

echo ""
info "🚀 Начало процесса миграции базы данных"
echo ""

# Шаг 1: Проверка статуса контейнеров
info "Шаг 1/7: Проверка статуса контейнеров..."
if ! docker compose ps | grep -q "Up"; then
    error "Контейнеры не запущены. Запустите их командой: docker compose up -d"
    exit 1
fi
success "Контейнеры запущены"
echo ""

# Шаг 2: Проверка текущей версии миграции
info "Шаг 2/7: Проверка текущей версии миграции..."
CURRENT_VERSION=$(docker compose exec -T api alembic current 2>/dev/null | grep -oP '\d+' | head -1)
info "Текущая версия миграции: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" = "002" ]; then
    success "Миграция уже применена (версия 002)"
    echo ""
    info "Проверка типа колонки telegram_id..."
    docker compose exec -T db psql -U subscriptions_user -d subscriptions -c "\d users" | grep telegram_id
    exit 0
fi
echo ""

# Шаг 3: Создание бэкапа
info "Шаг 3/7: Создание бэкапа базы данных..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
if docker compose exec -T db pg_dump -U subscriptions_user subscriptions > "$BACKUP_FILE" 2>/dev/null; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    success "Бэкап создан: $BACKUP_FILE (размер: $BACKUP_SIZE)"

    # Проверка размера бэкапа
    if [ ! -s "$BACKUP_FILE" ]; then
        error "Бэкап пустой! Прерывание миграции."
        rm "$BACKUP_FILE"
        exit 1
    fi
else
    error "Не удалось создать бэкап. Прерывание миграции."
    exit 1
fi
echo ""

# Шаг 4: Подтверждение пользователя
warning "⚠️  ВНИМАНИЕ: Сейчас будет применена миграция базы данных"
warning "   Это изменит тип колонки telegram_id с int32 на int64"
echo ""
read -p "Продолжить? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    info "Миграция отменена пользователем"
    exit 0
fi
echo ""

# Шаг 5: Применение миграции
info "Шаг 5/7: Применение миграции..."
if docker compose exec -T api alembic upgrade head 2>&1; then
    success "Миграция успешно применена"
else
    error "Ошибка при применении миграции"
    warning "Для отката используйте: docker compose exec api alembic downgrade -1"
    warning "Или восстановите из бэкапа: docker compose exec -T db psql -U subscriptions_user -d subscriptions < $BACKUP_FILE"
    exit 1
fi
echo ""

# Шаг 6: Проверка применения
info "Шаг 6/7: Проверка применения миграции..."
NEW_VERSION=$(docker compose exec -T api alembic current 2>/dev/null | grep -oP '\d+' | head -1)
if [ "$NEW_VERSION" = "002" ]; then
    success "Версия миграции обновлена: 001 -> 002"
else
    error "Версия миграции не обновилась. Текущая версия: $NEW_VERSION"
    exit 1
fi
echo ""

# Шаг 7: Перезапуск сервисов
info "Шаг 7/7: Перезапуск сервисов..."
docker compose restart api bot
sleep 3
success "Сервисы перезапущены"
echo ""

# Финальная проверка
info "🔍 Проверка типа колонки telegram_id..."
echo ""
docker compose exec -T db psql -U subscriptions_user -d subscriptions -c "\d users" | grep telegram_id || true
echo ""

# Проверка здоровья API
info "🏥 Проверка здоровья API..."
sleep 2
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    success "API работает корректно"
else
    warning "API не отвечает или вернул ошибку"
fi
echo ""

# Итоговое сообщение
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "🎉 Миграция успешно завершена!"
echo ""
info "📋 Результаты:"
info "   • Версия миграции: 002 (BigInteger)"
info "   • Бэкап сохранен: $BACKUP_FILE"
info "   • Сервисы перезапущены"
echo ""
info "📝 Следующие шаги:"
info "   1. Проверьте логи: docker compose logs -f api bot"
info "   2. Протестируйте функциональность бота"
info "   3. Сохраните бэкап в безопасное место"
echo ""
info "🔄 Для отката миграции:"
info "   docker compose exec api alembic downgrade -1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
