"""Bot middlewares."""
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.core.logging import get_logger
from src.metrics.prometheus import bot_command_duration_seconds, bot_commands_total

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Logging middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Log incoming messages."""
        if isinstance(event, Message):
            logger.info(
                "message_received",
                user_id=event.from_user.id if event.from_user else None,
                text=event.text,
            )

        try:
            result = await handler(event, data)
            if isinstance(event, Message) and event.text and event.text.startswith("/"):
                bot_commands_total.labels(command=event.text, status="success").inc()
            return result
        except Exception as e:
            if isinstance(event, Message) and event.text and event.text.startswith("/"):
                bot_commands_total.labels(command=event.text, status="error").inc()
            logger.error(
                "handler_error",
                user_id=event.from_user.id if hasattr(event, "from_user") and event.from_user else None,
                error=str(e),
            )
            raise


class ThrottlingMiddleware(BaseMiddleware):
    """Rate limiting middleware."""

    def __init__(self, rate: int = 30):
        self.rate = rate  # messages per minute
        self.user_messages: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Check rate limit."""
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()

        # Clean old messages (older than 1 minute)
        self.user_messages[user_id] = [
            timestamp
            for timestamp in self.user_messages[user_id]
            if now - timestamp < 60
        ]

        # Check rate
        if len(self.user_messages[user_id]) >= self.rate:
            logger.warning("rate_limit_exceeded", user_id=user_id)
            await event.answer("Слишком много запросов. Пожалуйста, подождите.")
            return

        self.user_messages[user_id].append(now)
        return await handler(event, data)


class MetricsMiddleware(BaseMiddleware):
    """Metrics middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Track command duration."""
        if not isinstance(event, Message) or not event.text or not event.text.startswith("/"):
            return await handler(event, data)

        command = event.text.split()[0]
        start_time = time.time()

        try:
            result = await handler(event, data)
            return result
        finally:
            duration = time.time() - start_time
            bot_command_duration_seconds.labels(command=command).observe(duration)
