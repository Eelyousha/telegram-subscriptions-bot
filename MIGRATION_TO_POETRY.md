# Миграция на Poetry

Проект успешно переведен с `pip` + `requirements.txt` на `Poetry` для современного управления зависимостями.

## Что изменилось

### Добавлены файлы

1. **`pyproject.toml`** - основной файл конфигурации проекта:
   - Метаданные проекта
   - Зависимости (production и dev)
   - Настройки инструментов (pytest, black, isort, ruff, mypy)
   - Build system configuration

2. **`Makefile`** - удобные команды для разработки:
   - `make install` - установка зависимостей
   - `make test` - запуск тестов
   - `make lint` - проверка кода
   - `make format` - форматирование кода
   - `make run-api` / `make run-bot` - запуск сервисов
   - И другие полезные команды

3. **`MIGRATION_TO_POETRY.md`** - этот файл с инструкциями

### Обновлены файлы

1. **`Dockerfile.api`** и **`Dockerfile.bot`**:
   - Теперь используют Poetry для установки зависимостей
   - Оптимизированы для production (без dev-зависимостей)

2. **`.dockerignore`**:
   - Добавлены исключения для Poetry (poetry.toml)
   - Добавлены кеши линтеров (.ruff_cache, .mypy_cache)

3. **`.gitignore`**:
   - Раскомментирован `poetry.toml` для игнорирования локальной конфигурации

4. **`README.md`**:
   - Обновлены инструкции по установке и запуску
   - Добавлена секция "Управление зависимостями"

### Файлы, которые можно удалить

- `requirements.txt` - теперь не нужен (можно оставить для обратной совместимости или удалить)
- `pytest.ini` - настройки перенесены в `pyproject.toml`

## Как использовать

### Первичная настройка

```bash
# 1. Установить Poetry (если ещё не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Установить зависимости
poetry install

# 3. Создать lock-файл (уже будет создан автоматически при install)
poetry lock
```

### Повседневная работа

```bash
# Активировать виртуальное окружение
poetry shell

# Или запускать команды через poetry run
poetry run python -m src.api.main
poetry run pytest

# Использовать Makefile для удобства
make install  # Установить зависимости
make test     # Запустить тесты
make lint     # Проверить код
make format   # Отформатировать код
```

### Управление зависимостями

```bash
# Добавить новую зависимость
poetry add requests

# Добавить dev-зависимость
poetry add --group dev pytest-mock

# Обновить все зависимости
poetry update

# Обновить конкретную зависимость
poetry update fastapi

# Показать список зависимостей
poetry show

# Показать дерево зависимостей
poetry show --tree
```

### Экспорт в requirements.txt

Если нужно сгенерировать `requirements.txt` для обратной совместимости:

```bash
# Только production зависимости
poetry export -f requirements.txt --output requirements.txt --without-hashes

# С dev-зависимостями
poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes
```

## Преимущества Poetry

1. **Dependency resolution** - автоматическое разрешение конфликтов версий
2. **Lock file** - `poetry.lock` гарантирует воспроизводимые установки
3. **Управление окружениями** - встроенное создание и управление venv
4. **Единый файл** - вся конфигурация в `pyproject.toml` (PEP 518)
5. **Dev dependencies** - разделение production и development зависимостей
6. **Скрипты** - определение entry points в конфигурации
7. **Build система** - встроенная поддержка создания wheel и sdist

## Структура pyproject.toml

```toml
[tool.poetry]              # Метаданные проекта
[tool.poetry.dependencies] # Production зависимости
[tool.poetry.group.dev]    # Dev зависимости
[tool.poetry.scripts]      # Entry points для команд
[build-system]             # Build backend конфигурация

# Настройки инструментов разработки
[tool.pytest.ini_options]  # Pytest
[tool.black]               # Black formatter
[tool.isort]               # Import sorter
[tool.ruff]                # Ruff linter
[tool.mypy]                # Type checker
```

## Docker и CI/CD

Dockerfile'ы обновлены для работы с Poetry:

```dockerfile
# Установка Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Копирование конфигурации
COPY pyproject.toml poetry.lock* ./

# Установка только production зависимостей без создания venv
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main
```

## Миграция команд

| Старая команда (pip) | Новая команда (Poetry) |
|---------------------|------------------------|
| `pip install -r requirements.txt` | `poetry install` |
| `pip install package` | `poetry add package` |
| `pip install --upgrade package` | `poetry update package` |
| `pip freeze > requirements.txt` | `poetry export -f requirements.txt` |
| `python -m venv .venv` | `poetry shell` (создаст автоматически) |

## Рекомендации

1. **Коммитить `poetry.lock`** - это гарантирует одинаковые версии у всех разработчиков
2. **Использовать `poetry.lock`** в production для воспроизводимых деплоев
3. **Регулярно обновлять зависимости** - `poetry update` и проверять breaking changes
4. **Использовать version constraints** - `^` для минорных обновлений, `~` для patch
5. **Группировать dev-зависимости** - держать production зависимости минимальными

## Troubleshooting

### Poetry не найден после установки

```bash
# Добавить в PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Конфликты зависимостей

```bash
# Очистить кеш и переустановить
poetry cache clear pypi --all
rm poetry.lock
poetry install
```

### Медленная установка

```bash
# Использовать параллельную установку
poetry config installer.max-workers 10
```

## Дополнительная информация

- [Официальная документация Poetry](https://python-poetry.org/docs/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- [Poetry команды](https://python-poetry.org/docs/cli/)
