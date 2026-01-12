"""Subscription CRUD repository."""
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import ErrorMessages, NotFoundException
from src.db.models import Subscription


class SubscriptionCRUDRepository:
    """Subscription repository for CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, telegram_id: int, data: dict[str, Any]) -> Subscription:
        """Create subscription.

        Args:
            telegram_id: Telegram user ID
            data: Subscription data

        Returns:
            Created subscription
        """
        subscription = Subscription(telegram_id=telegram_id, **data)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: int) -> Subscription | None:
        """Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription or None if not found
        """
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, subscription_id: int) -> Subscription:
        """Get subscription by ID or raise NotFoundException.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription object

        Raises:
            NotFoundException: If subscription not found
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise NotFoundException(ErrorMessages.SUBSCRIPTION_NOT_FOUND)
        return subscription

    async def get_all_by_user(self, telegram_id: int) -> list[Subscription]:
        """Get all active subscriptions for user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            List of active subscriptions
        """
        stmt = (
            select(Subscription)
            .where(
                and_(
                    Subscription.telegram_id == telegram_id,
                    Subscription.is_active == True,
                )
            )
            .order_by(Subscription.next_payment)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, subscription_id: int, data: dict[str, Any]
    ) -> Subscription | None:
        """Update subscription.

        Args:
            subscription_id: Subscription ID
            data: Updated data

        Returns:
            Updated subscription or None if not found
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(subscription, key, value)

        # updated_at is automatically set by SQLAlchemy onupdate
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def soft_delete(self, subscription_id: int) -> bool:
        """Mark subscription as inactive.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful, False if not found
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False

        subscription.is_active = False
        # updated_at is automatically set by SQLAlchemy onupdate
        await self.session.commit()
        return True

    async def get_pending_notifications(self, target_date: date) -> list[Subscription]:
        """Get subscriptions requiring notification.

        Args:
            target_date: Date to check notifications for

        Returns:
            List of subscriptions needing notifications
        """
        stmt = select(Subscription).where(
            and_(
                Subscription.is_active == True,
                func.date(Subscription.next_payment) - Subscription.notify_days
                <= target_date,
                Subscription.next_payment >= target_date,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def advance_next_payment(self, subscription_id: int) -> bool:
        """Advance next_payment by period_days.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful, False if not found
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False

        subscription.next_payment = subscription.next_payment + timedelta(
            days=subscription.period_days
        )
        # updated_at is automatically set by SQLAlchemy onupdate
        await self.session.commit()
        return True

    async def advance_past_payments(self) -> int:
        """Advance all past payments to next period.

        Returns:
            Number of subscriptions updated
        """
        today = date.today()
        stmt = select(Subscription).where(
            and_(
                Subscription.is_active == True,
                Subscription.next_payment < today,
            )
        )
        result = await self.session.execute(stmt)
        subscriptions = result.scalars().all()

        count = 0
        for sub in subscriptions:
            # Advance until next_payment is in the future
            while sub.next_payment < today:
                sub.next_payment = sub.next_payment + timedelta(days=sub.period_days)
            # updated_at is automatically set by SQLAlchemy onupdate
            count += 1

        await self.session.commit()
        return count
