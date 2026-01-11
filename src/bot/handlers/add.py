"""Add subscription handler."""
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.api_client import APIClient
from src.bot.keyboards import currency_keyboard, period_keyboard, today_keyboard
from src.bot.states import AddSubscription
from src.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    """Start adding subscription."""
    await message.answer("📝 Введите название сервиса")
    await state.set_state(AddSubscription.name)


@router.message(AddSubscription.name)
async def process_name(message: Message, state: FSMContext):
    """Process subscription name."""
    if not message.text or len(message.text) > 100:
        await message.answer("Название должно быть от 1 до 100 символов")
        return

    await state.update_data(name=message.text)
    await message.answer("💰 Введите сумму списания")
    await state.set_state(AddSubscription.amount)


@router.message(AddSubscription.amount)
async def process_amount(message: Message, state: FSMContext):
    """Process subscription amount."""
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Введите корректную сумму (число больше 0)")
        return

    await state.update_data(amount=amount)
    await message.answer("💱 Выберите валюту", reply_markup=currency_keyboard())
    await state.set_state(AddSubscription.currency)


@router.callback_query(AddSubscription.currency, F.data.startswith("currency:"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    """Process currency selection."""
    currency = callback.data.split(":")[1]
    await state.update_data(currency=currency)

    await callback.message.edit_text(f"💱 Валюта: {currency}")
    await callback.message.answer(
        "🔄 Как часто списывается?", reply_markup=period_keyboard()
    )
    await state.set_state(AddSubscription.period)
    await callback.answer()


@router.callback_query(AddSubscription.period, F.data.startswith("period:"))
async def process_period(callback: CallbackQuery, state: FSMContext):
    """Process period selection."""
    period_data = callback.data.split(":")[1]

    if period_data == "custom":
        await callback.message.edit_text("🔄 Период: произвольный")
        await callback.message.answer("Введите количество дней (1-365)")
        await state.set_state(AddSubscription.custom_period)
    else:
        period_days = int(period_data)
        period_text = {"7": "неделя", "30": "месяц", "365": "год"}[period_data]

        await state.update_data(period_days=period_days)
        await callback.message.edit_text(f"🔄 Период: {period_text}")
        await callback.message.answer(
            "📅 Введите дату следующего списания (ДД.ММ.ГГГГ)",
            reply_markup=today_keyboard(),
        )
        await state.set_state(AddSubscription.next_payment)

    await callback.answer()


@router.message(AddSubscription.custom_period)
async def process_custom_period(message: Message, state: FSMContext):
    """Process custom period."""
    try:
        period_days = int(message.text)
        if not 1 <= period_days <= 365:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Введите число от 1 до 365")
        return

    await state.update_data(period_days=period_days)
    await message.answer(
        "📅 Введите дату следующего списания (ДД.ММ.ГГГГ)",
        reply_markup=today_keyboard(),
    )
    await state.set_state(AddSubscription.next_payment)


@router.message(AddSubscription.next_payment)
async def process_next_payment(message: Message, state: FSMContext):
    """Process next payment date."""
    if message.text == "Сегодня":
        next_payment = date.today()
    else:
        try:
            next_payment = datetime.strptime(message.text, "%d.%m.%Y").date()
            if next_payment < date.today():
                await message.answer("Дата не может быть в прошлом")
                return
        except ValueError:
            await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ")
            return

    await state.update_data(next_payment=next_payment.isoformat())
    await message.answer(
        "🔔 За сколько дней напомнить? (по умолчанию 3)",
        reply_markup={"remove_keyboard": True},
    )
    await state.set_state(AddSubscription.notify_days)


@router.message(AddSubscription.notify_days)
async def process_notify_days(message: Message, state: FSMContext, api_client: APIClient):
    """Process notify days and create subscription."""
    try:
        notify_days = int(message.text) if message.text else 3
        if notify_days < 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("Введите число >= 0 или оставьте пустым для значения по умолчанию (3)")
        return

    data = await state.get_data()

    # Validate notify_days <= period_days
    if notify_days > data["period_days"]:
        await message.answer(
            f"Дни уведомления не могут превышать период ({data['period_days']} дней)"
        )
        return

    # Create subscription via API
    subscription_data = {
        "name": data["name"],
        "amount": data["amount"],
        "currency": data["currency"],
        "period_days": data["period_days"],
        "next_payment": data["next_payment"],
        "notify_days": notify_days,
    }

    try:
        subscription = await api_client.create_subscription(
            telegram_id=message.from_user.id,
            data=subscription_data,
        )

        # Format response
        period_text = {7: "неделю", 30: "месяц", 365: "год"}.get(
            data["period_days"], f"{data['period_days']} дн."
        )

        next_payment_date = datetime.fromisoformat(data["next_payment"])
        text = (
            f"✅ Подписка добавлена!\n\n"
            f"{data['name']} — {data['amount']} {data['currency']}/{period_text}\n"
            f"Следующее списание: {next_payment_date.strftime('%d.%m.%Y')}\n"
            f"Напомню за {notify_days} дн."
        )

        await message.answer(text)
        logger.info("subscription_created", user_id=message.from_user.id, subscription_id=subscription["id"])

    except Exception as e:
        logger.error("subscription_creation_failed", user_id=message.from_user.id, error=str(e))
        await message.answer("❌ Ошибка при создании подписки. Попробуйте позже.")

    await state.clear()
