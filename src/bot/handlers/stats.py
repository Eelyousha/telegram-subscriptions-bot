"""Statistics handler."""
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.api import SubscriptionAPIClient
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, subscription_client: SubscriptionAPIClient):
    """Show user statistics."""
    if not message.from_user:
        return

    stats = await subscription_client.get_stats(message.from_user.id)

    if stats["total_subscriptions"] == 0:
        await message.answer("У вас пока нет подписок. Добавьте первую командой /add")
        return

    text = "📊 Статистика подписок\n\n"
    text += f"Всего активных: {stats['total_subscriptions']}\n"

    # By currency
    if stats["by_currency"]:
        text += "\n💳 По валютам:\n"
        for curr_stat in stats["by_currency"]:
            currency_symbol = {"RUB": "₽", "USD": "$", "EUR": "€"}.get(
                curr_stat["currency"], curr_stat["currency"]
            )
            text += f"• {curr_stat['currency']}: {curr_stat['total_monthly']:.2f} {currency_symbol}/мес ({curr_stat['count']} шт.)\n"

    # Total in RUB
    if stats["total_monthly_rub"] > 0:
        text += f"\nОбщая сумма: ~{stats['total_monthly_rub']:.2f} ₽/мес\n"

    # Upcoming payments
    if stats["upcoming_payments"]:
        text += "\n📅 Ближайшие списания:\n"
        for payment in stats["upcoming_payments"]:
            payment_date = date.fromisoformat(payment["date"])
            currency_symbol = {"RUB": "₽", "USD": "$", "EUR": "€"}.get(
                payment["currency"], payment["currency"]
            )
            text += f"• {payment_date.strftime('%d.%m')} — {payment['name']} ({payment['amount']} {currency_symbol})\n"

    await message.answer(text)
    logger.info("stats_command", user_id=message.from_user.id)
