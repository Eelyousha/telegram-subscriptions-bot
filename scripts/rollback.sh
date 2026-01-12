#!/bin/bash

# Скрипт для отката миграции базы данных
# Использование: ./scripts/rollback.sh

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
warning "🔙 ОТКАТ МИГРАЦИИ БАЗЫ ДАННЫХ"
echo ""

# Проверка текущей версии
info "Проверка текущей версии миграции..."
CURRENT_VERSION=$(docker compose exec -T api alembic current 2>/dev/null | grep -oP '\d+' | head -1)
info "Текущая версия: $CURRENT_VERSION"
echo ""

if [ "$CURRENT_VERSION" != "002" ]; then
    warning "Миграция 002 не применена. Текущая версия: $CURRENT_VERSION"
    info "Откат не требуется."
    exit 0
fi

# ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warning "⚠️  ВНИМАНИЕ! ВАЖНАЯ ИНФОРМАЦИЯ:"
echo ""
warning "Откат миграции вернет тип telegram_id с int64 на int32"
warning "Это НЕ СРАБОТАЕТ, если в базе есть telegram_id > 2,147,483,647"
echo ""
info "Проверка максимального telegram_id в базе..."
MAX_ID=$(docker compose exec -T db psql -U subscriptions_user -d subscriptions -t -c "SELECT MAX(telegram_id) FROM users;" 2>/dev/null | tr -d ' \n')

if [ -n "$MAX_ID" ] && [ "$MAX_ID" != "" ]; then
    info "Максимальный telegram_id: $MAX_ID"
    INT32_MAX=2147483647

    if [ "$MAX_ID" -gt "$INT32_MAX" ]; then
        error "В базе есть telegram_id больше int32 максимума!"
        error "Максимальный ID: $MAX_ID > 2,147,483,647"
        error "ОТКАТ НЕВОЗМОЖЕН без потери данных!"
        echo ""
        warning "Рекомендация: оставьте BigInteger (int64)"
        exit 1
    else
        success "Все telegram_id помещаются в int32 (< 2,147,483,647)"
    fi
else
    info "Пользователей не найдено в базе"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Подтверждение
warning "Вы уверены, что хотите откатить миграцию?"
read -p "Введите 'ROLLBACK' для подтверждения: " CONFIRM

if [ "$CONFIRM" != "ROLLBACK" ]; then
    info "Откат отменен"
    exit 0
fi
echo ""

# Создание бэкапа перед откатом
info "Создание бэкапа перед откатом..."
BACKUP_FILE="backup_before_rollback_$(date +%Y%m%d_%H%M%S).sql"
if docker compose exec -T db pg_dump -U subscriptions_user subscriptions > "$BACKUP_FILE" 2>/dev/null; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    success "Бэкап создан: $BACKUP_FILE (размер: $BACKUP_SIZE)"
else
    error "Не удалось создать бэкап. Прерывание отката."
    exit 1
fi
echo ""

# Остановка сервисов
info "Остановка API и Bot..."
docker compose stop api bot
success "Сервисы остановлены"
echo ""

# Откат миграции
info "Откат миграции 002 -> 001..."
if docker compose exec -T api alembic downgrade -1 2>&1; then
    success "Миграция откачена"
else
    error "Ошибка при откате миграции"
    warning "Попытка восстановления из бэкапа..."
    docker compose exec -T db psql -U subscriptions_user -d subscriptions < "$BACKUP_FILE"
    exit 1
fi
echo ""

# Проверка версии
info "Проверка версии после отката..."
NEW_VERSION=$(docker compose exec -T api alembic current 2>/dev/null | grep -oP '\d+' | head -1)
if [ "$NEW_VERSION" = "001" ]; then
    success "Версия миграции: 002 -> 001"
else
    error "Версия не изменилась. Текущая версия: $NEW_VERSION"
    exit 1
fi
echo ""

# Запуск сервисов
info "Запуск сервисов..."
docker compose start api bot
sleep 3
success "Сервисы запущены"
echo ""

# Проверка типа колонки
info "Проверка типа колонки telegram_id..."
docker compose exec -T db psql -U subscriptions_user -d subscriptions -c "\d users" | grep telegram_id || true
echo ""

# Итог
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "✅ Откат миграции завершен"
echo ""
info "📋 Результаты:"
info "   • Версия миграции: 001 (Integer)"
info "   • Бэкап сохранен: $BACKUP_FILE"
info "   • Сервисы перезапущены"
echo ""
warning "⚠️  ВАЖНО:"
warning "   telegram_id теперь ограничен значением 2,147,483,647"
warning "   Новые пользователи с большими ID вызовут ошибку!"
echo ""
info "🔄 Для повторного применения миграции:"
info "   docker compose exec api alembic upgrade head"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
