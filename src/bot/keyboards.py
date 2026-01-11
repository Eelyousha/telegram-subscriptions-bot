"""Keyboard layouts for bot."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def currency_keyboard() -> InlineKeyboardMarkup:
    """Currency selection keyboard."""
    buttons = [
        [InlineKeyboardButton(text="RUB", callback_data="currency:RUB")],
        [InlineKeyboardButton(text="USD", callback_data="currency:USD")],
        [InlineKeyboardButton(text="EUR", callback_data="currency:EUR")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def period_keyboard() -> InlineKeyboardMarkup:
    """Period selection keyboard."""
    buttons = [
        [InlineKeyboardButton(text="Неделя", callback_data="period:7")],
        [InlineKeyboardButton(text="Месяц", callback_data="period:30")],
        [InlineKeyboardButton(text="Год", callback_data="period:365")],
        [InlineKeyboardButton(text="Другое", callback_data="period:custom")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def today_keyboard() -> ReplyKeyboardMarkup:
    """Today button keyboard."""
    buttons = [[KeyboardButton(text="Сегодня")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def subscriptions_keyboard(subscriptions: list[dict]) -> InlineKeyboardMarkup:
    """Subscriptions list keyboard."""
    buttons = [
        [InlineKeyboardButton(text=f"{sub['name']} — {sub['amount']} {sub['currency']}",
                             callback_data=f"sub:{sub['id']}")]
        for sub in subscriptions
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard(action: str, subscription_id: int) -> InlineKeyboardMarkup:
    """Confirmation keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="Да", callback_data=f"{action}:yes:{subscription_id}"),
            InlineKeyboardButton(text="Нет", callback_data=f"{action}:no:{subscription_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_fields_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    """Edit subscription fields keyboard."""
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"edit:name:{subscription_id}")],
        [InlineKeyboardButton(text="Сумма", callback_data=f"edit:amount:{subscription_id}")],
        [InlineKeyboardButton(text="Валюта", callback_data=f"edit:currency:{subscription_id}")],
        [InlineKeyboardButton(text="Период", callback_data=f"edit:period:{subscription_id}")],
        [InlineKeyboardButton(text="Дата списания", callback_data=f"edit:next_payment:{subscription_id}")],
        [InlineKeyboardButton(text="Дни уведомления", callback_data=f"edit:notify_days:{subscription_id}")],
        [InlineKeyboardButton(text="Готово", callback_data=f"edit:done:{subscription_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
