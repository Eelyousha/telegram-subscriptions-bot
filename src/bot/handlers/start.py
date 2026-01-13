"""Start command handler."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.api import UserAPIClient
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, user_client: UserAPIClient):
    """Handle /start command."""
    if not message.from_user:
        return

    # Register user
    await user_client.create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    text = (
        "👋 Привет! Я помогу отслеживать твои подписки.\n\n"
        "Что я умею:\n"
        "• /add — добавить подписку\n"
        "• /list — список подписок\n"
        "• /stats — статистика расходов\n"
        "• /edit — редактировать подписку\n"
        "• /delete — удалить подписку\n\n"
        "Начни с добавления первой подписки: /add"
    )

    await message.answer(text)
    logger.info("start_command", user_id=message.from_user.id)
