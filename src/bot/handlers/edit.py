"""Edit subscription handler."""
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.api_client import APIClient
from src.bot.keyboards import (
    currency_keyboard,
    edit_fields_keyboard,
    period_keyboard,
    subscriptions_keyboard,
)
from src.bot.states import EditSubscription
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("edit"))
async def cmd_edit(message: Message, api_client: APIClient, state: FSMContext):
    """Start editing subscription."""
    if not message.from_user:
        return

    subscriptions = await api_client.get_subscriptions(message.from_user.id)

    if not subscriptions:
        await message.answer("У вас нет подписок")
        return

    await message.answer(
        "Выберите подписку для редактирования:",
        reply_markup=subscriptions_keyboard(subscriptions),
    )
    await state.set_state(EditSubscription.select_subscription)


@router.callback_query(EditSubscription.select_subscription, F.data.startswith("sub:"))
async def select_subscription(callback: CallbackQuery, api_client: APIClient, state: FSMContext):
    """Show edit menu."""
    subscription_id = int(callback.data.split(":")[1])

    # Get subscription details
    subscriptions = await api_client.get_subscriptions(callback.from_user.id)
    subscription = next((s for s in subscriptions if s["id"] == subscription_id), None)

    if not subscription:
        await callback.answer("Подписка не найдена")
        return

    await state.update_data(subscription_id=subscription_id, subscription=subscription)

    text = (
        f"Редактирование: {subscription['name']}\n\n"
        f"Сумма: {subscription['amount']} {subscription['currency']}\n"
        f"Период: {subscription['period_days']} дн.\n"
        f"Дата списания: {subscription['next_payment']}\n"
        f"Дни уведомления: {subscription['notify_days']}\n\n"
        f"Выберите поле для изменения:"
    )

    await callback.message.edit_text(
        text, reply_markup=edit_fields_keyboard(subscription_id)
    )
    await state.set_state(EditSubscription.select_field)
    await callback.answer()


@router.callback_query(EditSubscription.select_field, F.data.startswith("edit:"))
async def select_field(callback: CallbackQuery, state: FSMContext):
    """Select field to edit."""
    parts = callback.data.split(":")
    field = parts[1]
    subscription_id = int(parts[2])

    if field == "done":
        await callback.message.edit_text("✅ Редактирование завершено")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(field=field, subscription_id=subscription_id)

    if field == "currency":
        await callback.message.edit_text("Выберите новую валюту:", reply_markup=currency_keyboard())
    elif field == "period":
        await callback.message.edit_text("Выберите новый период:", reply_markup=period_keyboard())
    else:
        field_names = {
            "name": "название",
            "amount": "сумму",
            "next_payment": "дату следующего списания (ДД.ММ.ГГГГ)",
            "notify_days": "дни уведомления",
        }
        await callback.message.edit_text(f"Введите новое значение ({field_names.get(field, field)}):")

    await state.set_state(EditSubscription.edit_value)
    await callback.answer()


@router.callback_query(EditSubscription.edit_value, F.data.startswith("currency:"))
async def edit_currency(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Edit currency."""
    currency = callback.data.split(":")[1]
    data = await state.get_data()
    subscription_id = data["subscription_id"]

    try:
        await api_client.update_subscription(subscription_id, {"currency": currency})
        await callback.message.edit_text(f"✅ Валюта изменена на {currency}")
        logger.info("subscription_updated", user_id=callback.from_user.id, subscription_id=subscription_id)
    except Exception as e:
        logger.error("subscription_update_failed", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text("❌ Ошибка при обновлении")

    await state.clear()
    await callback.answer()


@router.callback_query(EditSubscription.edit_value, F.data.startswith("period:"))
async def edit_period(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Edit period."""
    period_data = callback.data.split(":")[1]

    if period_data == "custom":
        await callback.message.edit_text("Введите количество дней (1-365):")
        await callback.answer()
        return

    period_days = int(period_data)
    data = await state.get_data()
    subscription_id = data["subscription_id"]

    try:
        await api_client.update_subscription(subscription_id, {"period_days": period_days})
        await callback.message.edit_text(f"✅ Период изменен на {period_days} дн.")
        logger.info("subscription_updated", user_id=callback.from_user.id, subscription_id=subscription_id)
    except Exception as e:
        logger.error("subscription_update_failed", user_id=callback.from_user.id, error=str(e))
        await callback.message.edit_text("❌ Ошибка при обновлении")

    await state.clear()
    await callback.answer()


@router.message(EditSubscription.edit_value)
async def edit_value(message: Message, state: FSMContext, api_client: APIClient):
    """Process field value edit."""
    data = await state.get_data()
    field = data["field"]
    subscription_id = data["subscription_id"]

    update_data = {}

    try:
        if field == "name":
            if len(message.text) > 100:
                await message.answer("Название должно быть до 100 символов")
                return
            update_data["name"] = message.text

        elif field == "amount":
            amount = float(message.text.replace(",", "."))
            if amount <= 0:
                raise ValueError
            update_data["amount"] = amount

        elif field == "period":
            period_days = int(message.text)
            if not 1 <= period_days <= 365:
                raise ValueError
            update_data["period_days"] = period_days

        elif field == "next_payment":
            next_payment = datetime.strptime(message.text, "%d.%m.%Y").date()
            update_data["next_payment"] = next_payment.isoformat()

        elif field == "notify_days":
            notify_days = int(message.text)
            if notify_days < 0:
                raise ValueError
            update_data["notify_days"] = notify_days

        await api_client.update_subscription(subscription_id, update_data)
        await message.answer("✅ Поле обновлено")
        logger.info("subscription_updated", user_id=message.from_user.id, subscription_id=subscription_id)

    except ValueError:
        await message.answer("❌ Неверный формат значения")
    except Exception as e:
        logger.error("subscription_update_failed", user_id=message.from_user.id, error=str(e))
        await message.answer("❌ Ошибка при обновлении")

    await state.clear()
