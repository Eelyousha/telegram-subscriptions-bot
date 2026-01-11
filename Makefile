.PHONY: help install update shell test lint format clean run-api run-bot docker-build docker-up docker-down migrate

help: ## Показать эту справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	poetry install

update: ## Обновить зависимости
	poetry update

shell: ## Активировать виртуальное окружение
	poetry shell

test: ## Запустить тесты
	poetry run pytest

lint: ## Проверить код линтерами
	poetry run ruff check src/ tests/
	poetry run mypy src/

format: ## Форматировать код
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

clean: ## Очистить временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

run-api: ## Запустить API сервер
	poetry run python -m src.api.main

run-bot: ## Запустить Telegram бота
	poetry run python -m src.bot.main

docker-build: ## Собрать Docker образы
	docker-compose build

docker-up: ## Запустить все сервисы в Docker
	docker-compose up -d

docker-down: ## Остановить все сервисы
	docker-compose down

migrate: ## Применить миграции БД
	poetry run alembic upgrade head

migrate-create: ## Создать новую миграцию (использование: make migrate-create MSG="description")
	poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Откатить последнюю миграцию
	poetry run alembic downgrade -1

db-shell: ## Подключиться к PostgreSQL
	docker exec -it subscriptions-db psql -U subscriptions_user -d subscriptions
