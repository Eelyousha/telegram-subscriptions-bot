"""API schemas (Pydantic models)."""
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Currency(str, Enum):
    """Currency enum."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Period(int, Enum):
    """Predefined periods."""

    WEEKLY = 7
    MONTHLY = 30
    YEARLY = 365


# === Users ===


class UserCreate(BaseModel):
    """User creation schema."""

    telegram_id: int
    username: str | None = None
    first_name: str | None = None


class User(BaseModel):
    """User response schema."""

    telegram_id: int
    username: str | None
    first_name: str | None
    last_seen: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# === Subscriptions ===


class SubscriptionCreate(BaseModel):
    """Subscription creation schema."""

    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    currency: Currency = Currency.RUB
    period_days: int = Field(..., gt=0, le=365)
    next_payment: date
    notify_days: int = Field(default=3, ge=0)

    @field_validator("next_payment")
    @classmethod
    def payment_not_in_past(cls, v: date) -> date:
        """Validate that payment date is not in the past."""
        if v < date.today():
            raise ValueError("next_payment cannot be in the past")
        return v

    @field_validator("notify_days")
    @classmethod
    def notify_within_period(cls, v: int, info) -> int:
        """Validate that notify_days doesn't exceed period."""
        period = info.data.get("period_days")
        if period and v > period:
            raise ValueError("notify_days cannot exceed period_days")
        return v


class SubscriptionUpdate(BaseModel):
    """Subscription update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)
    amount: float | None = Field(None, gt=0)
    currency: Currency | None = None
    period_days: int | None = Field(None, gt=0, le=365)
    next_payment: date | None = None
    notify_days: int | None = Field(None, ge=0)


class Subscription(BaseModel):
    """Subscription response schema."""

    id: int
    telegram_id: int
    name: str
    amount: float
    currency: Currency
    period_days: int
    next_payment: date
    notify_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Stats ===


class CurrencyStats(BaseModel):
    """Statistics per currency."""

    currency: Currency
    total_monthly: float
    count: int


class UpcomingPayment(BaseModel):
    """Upcoming payment info."""

    subscription_id: int
    name: str
    amount: float
    currency: Currency
    date: date
    days_left: int


class UserStats(BaseModel):
    """User statistics."""

    total_subscriptions: int
    total_monthly_rub: float
    by_currency: list[CurrencyStats]
    upcoming_payments: list[UpcomingPayment]
