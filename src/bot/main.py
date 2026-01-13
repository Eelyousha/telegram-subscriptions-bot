"""Telegram bot entry point."""
import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.api import SubscriptionAPIClient, UserAPIClient
from src.bot.handlers import add, delete, edit, list, start, stats
from src.bot.middlewares import LoggingMiddleware, MetricsMiddleware, ThrottlingMiddleware
from src.core.config import settings
from src.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def main():
    """Main bot function."""
    configure_logging()
    logger.info("bot_starting")

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Create API clients
    user_client = UserAPIClient()
    subscription_client = SubscriptionAPIClient()

    # Register middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate=settings.throttle_rate))
    dp.message.middleware(MetricsMiddleware())

    # Inject API clients into handlers
    dp["user_client"] = user_client
    dp["subscription_client"] = subscription_client

    # Register routers
    dp.include_router(start.router)
    dp.include_router(add.router)
    dp.include_router(list.router)
    dp.include_router(stats.router)
    dp.include_router(edit.router)
    dp.include_router(delete.router)

    # Start polling
    try:
        logger.info("bot_started")
        await dp.start_polling(
            bot, user_client=user_client, subscription_client=subscription_client
        )
    finally:
        logger.info("bot_shutting_down")
        await user_client.close()
        await subscription_client.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("bot_stopped")
        sys.exit(0)
