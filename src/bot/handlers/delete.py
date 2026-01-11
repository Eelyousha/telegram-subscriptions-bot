"""Delete subscription handler."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.api_client import APIClient
from src.bot.keyboards import confirm_keyboard, subscriptions_keyboard
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("delete"))
async def cmd_delete(message: Message, api_client: APIClient):
    """Start deleting subscription."""
    if not message.from_user:
        return

    subscriptions = await api_client.get_subscriptions(message.from_user.id)

    if not subscriptions:
        await message.answer("У вас нет подписок")
        return

    await message.answer(
        "Выберите подписку для удаления:",
        reply_markup=subscriptions_keyboard(subscriptions),
    )


@router.callback_query(F.data.startswith("sub:"))
async def select_subscription(callback: CallbackQuery, api_client: APIClient):
    """Confirm deletion."""
    subscription_id = int(callback.data.split(":")[1])

    # Get subscription details
    subscriptions = await api_client.get_subscriptions(callback.from_user.id)
    subscription = next((s for s in subscriptions if s["id"] == subscription_id), None)

    if not subscription:
        await callback.answer("Подписка не найдена")
        return

    await callback.message.edit_text(
        f"Удалить подписку {subscription['name']}?",
        reply_markup=confirm_keyboard("delete", subscription_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete:"))
async def confirm_deletion(callback: CallbackQuery, api_client: APIClient):
    """Process deletion confirmation."""
    parts = callback.data.split(":")
    action = parts[1]
    subscription_id = int(parts[2])

    if action == "no":
        await callback.message.edit_text("Удаление отменено")
        await callback.answer()
        return

    try:
        await api_client.delete_subscription(subscription_id)
        await callback.message.edit_text("✅ Подписка удалена")
        logger.info("subscription_deleted", user_id=callback.from_user.id, subscription_id=subscription_id)
    except Exception as e:
        logger.error("subscription_deletion_failed", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text("❌ Ошибка при удалении подписки")

    await callback.answer()
