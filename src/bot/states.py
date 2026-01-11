"""FSM states for bot dialogs."""
from aiogram.fsm.state import State, StatesGroup


class AddSubscription(StatesGroup):
    """States for adding a subscription."""

    name = State()
    amount = State()
    currency = State()
    period = State()
    custom_period = State()
    next_payment = State()
    notify_days = State()


class EditSubscription(StatesGroup):
    """States for editing a subscription."""

    select_subscription = State()
    select_field = State()
    edit_value = State()
