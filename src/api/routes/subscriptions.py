"""Subscription routes."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import schemas
from src.api.dependencies import get_db
from src.api.exceptions import NotFoundException
from src.db.repository import SubscriptionRepository

router = APIRouter(tags=["subscriptions"])


@router.get("/users/{telegram_id}/subscriptions", response_model=list[schemas.Subscription])
async def get_user_subscriptions(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[schemas.Subscription]:
    """Get all subscriptions for a user."""
    repo = SubscriptionRepository(session)
    subscriptions = await repo.get_all_by_user(telegram_id)
    return [schemas.Subscription.model_validate(sub) for sub in subscriptions]


@router.post("/users/{telegram_id}/subscriptions", response_model=schemas.Subscription)
async def create_subscription(
    telegram_id: int,
    subscription_data: schemas.SubscriptionCreate,
    session: AsyncSession = Depends(get_db),
) -> schemas.Subscription:
    """Create a new subscription."""
    repo = SubscriptionRepository(session)
    subscription = await repo.create(
        telegram_id=telegram_id,
        data=subscription_data.model_dump(),
    )
    return schemas.Subscription.model_validate(subscription)


@router.get("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def get_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_db),
) -> schemas.Subscription:
    """Get a subscription by ID."""
    repo = SubscriptionRepository(session)
    subscription = await repo.get_by_id(subscription_id)
    if not subscription:
        raise NotFoundException("Subscription not found")
    return schemas.Subscription.model_validate(subscription)


@router.patch("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def update_subscription(
    subscription_id: int,
    subscription_data: schemas.SubscriptionUpdate,
    session: AsyncSession = Depends(get_db),
) -> schemas.Subscription:
    """Update a subscription."""
    repo = SubscriptionRepository(session)
    subscription = await repo.update(
        subscription_id=subscription_id,
        data=subscription_data.model_dump(exclude_none=True),
    )
    if not subscription:
        raise NotFoundException("Subscription not found")
    return schemas.Subscription.model_validate(subscription)


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete (soft) a subscription."""
    repo = SubscriptionRepository(session)
    success = await repo.soft_delete(subscription_id)
    if not success:
        raise NotFoundException("Subscription not found")
    return {"ok": True}


@router.get("/users/{telegram_id}/stats", response_model=schemas.UserStats)
async def get_user_stats(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
) -> schemas.UserStats:
    """Get user statistics."""
    repo = SubscriptionRepository(session)
    subscriptions = await repo.get_all_by_user(telegram_id)

    # Calculate stats
    total_subscriptions = len(subscriptions)

    # Group by currency
    currency_stats: dict[str, dict] = {}
    for sub in subscriptions:
        if sub.currency not in currency_stats:
            currency_stats[sub.currency] = {"total": 0.0, "count": 0}

        # Convert to monthly
        if sub.period_days == 7:
            monthly = sub.amount * 4.33
        elif sub.period_days == 365:
            monthly = sub.amount / 12
        else:
            monthly = sub.amount * (30 / sub.period_days)

        currency_stats[sub.currency]["total"] += monthly
        currency_stats[sub.currency]["count"] += 1

    by_currency = [
        schemas.CurrencyStats(
            currency=schemas.Currency(curr),
            total_monthly=stats["total"],
            count=stats["count"],
        )
        for curr, stats in currency_stats.items()
    ]

    # Upcoming payments (next 30 days, max 5)
    today = date.today()
    upcoming = [
        schemas.UpcomingPayment(
            subscription_id=sub.id,
            name=sub.name,
            amount=sub.amount,
            currency=schemas.Currency(sub.currency),
            date=sub.next_payment,
            days_left=(sub.next_payment - today).days,
        )
        for sub in subscriptions
        if (sub.next_payment - today).days <= 30
    ]
    upcoming.sort(key=lambda x: x.date)
    upcoming = upcoming[:5]

    # Total monthly in RUB (simplified, no conversion)
    total_monthly_rub = currency_stats.get("RUB", {}).get("total", 0.0)

    return schemas.UserStats(
        total_subscriptions=total_subscriptions,
        total_monthly_rub=total_monthly_rub,
        by_currency=by_currency,
        upcoming_payments=upcoming,
    )
