"""List subscriptions handler."""
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.api_client import APIClient
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("list"))
async def cmd_list(message: Message, api_client: APIClient):
    """Show user's subscriptions."""
    if not message.from_user:
        return

    subscriptions = await api_client.get_subscriptions(message.from_user.id)

    if not subscriptions:
        await message.answer("У вас пока нет подписок. Добавьте первую командой /add")
        return

    text = f"📋 Ваши подписки ({len(subscriptions)}):\n\n"

    for i, sub in enumerate(subscriptions, 1):
        next_payment = date.fromisoformat(sub["next_payment"])
        days_left = (next_payment - date.today()).days

        period_text = {7: "неделю", 30: "месяц", 365: "год"}.get(
            sub["period_days"], f"{sub['period_days']} дн."
        )

        text += (
            f"{i}. {sub['name']} — {sub['amount']} {sub['currency']}/{period_text}\n"
            f"   Следующее списание: {next_payment.strftime('%d.%m.%Y')} "
            f"(через {days_left} дн.)\n\n"
        )

    await message.answer(text)
    logger.info("list_command", user_id=message.from_user.id, count=len(subscriptions))
