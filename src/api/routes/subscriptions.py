"""Subscription routes."""
from fastapi import APIRouter, Depends

from src.api import schemas
from src.api.dependencies import get_subscription_service
from src.services import SubscriptionService

router = APIRouter(tags=["subscriptions"])


@router.get("/users/{telegram_id}/subscriptions", response_model=list[schemas.Subscription])
async def get_user_subscriptions(
    telegram_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
) -> list[schemas.Subscription]:
    """Get all subscriptions for a user."""
    subscriptions = await service.get_user_subscriptions(telegram_id)
    return [schemas.Subscription.model_validate(sub) for sub in subscriptions]


@router.post("/users/{telegram_id}/subscriptions", response_model=schemas.Subscription)
async def create_subscription(
    telegram_id: int,
    subscription_data: schemas.SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service),
) -> schemas.Subscription:
    """Create a new subscription."""
    subscription = await service.create_subscription(
        telegram_id=telegram_id,
        data=subscription_data.model_dump(),
    )
    return schemas.Subscription.model_validate(subscription)


@router.get("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def get_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
) -> schemas.Subscription:
    """Get a subscription by ID."""
    subscription = await service.get_subscription(subscription_id)
    return schemas.Subscription.model_validate(subscription)


@router.patch("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def update_subscription(
    subscription_id: int,
    subscription_data: schemas.SubscriptionUpdate,
    service: SubscriptionService = Depends(get_subscription_service),
) -> schemas.Subscription:
    """Update a subscription."""
    subscription = await service.update_subscription(
        subscription_id=subscription_id,
        data=subscription_data.model_dump(exclude_none=True),
    )
    return schemas.Subscription.model_validate(subscription)


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, bool]:
    """Delete (soft) a subscription."""
    await service.delete_subscription(subscription_id)
    return {"ok": True}


@router.get("/users/{telegram_id}/stats", response_model=schemas.UserStats)
async def get_user_stats(
    telegram_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
) -> schemas.UserStats:
    """Get user statistics."""
    stats = await service.calculate_user_stats(telegram_id)

    # Convert to schema format
    by_currency = [
        schemas.CurrencyStats(
            currency=schemas.Currency(item["currency"]),
            total_monthly=item["total_monthly"],
            count=item["count"],
        )
        for item in stats["by_currency"]
    ]

    upcoming_payments = [
        schemas.UpcomingPayment(
            subscription_id=item["subscription_id"],
            name=item["name"],
            amount=item["amount"],
            currency=schemas.Currency(item["currency"]),
            date=item["date"],
            days_left=item["days_left"],
        )
        for item in stats["upcoming_payments"]
    ]

    return schemas.UserStats(
        total_subscriptions=stats["total_subscriptions"],
        total_monthly_rub=stats["total_monthly_rub"],
        by_currency=by_currency,
        upcoming_payments=upcoming_payments,
    )
