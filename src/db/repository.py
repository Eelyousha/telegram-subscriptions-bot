"""Database repository layer."""
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import ErrorMessages, NotFoundException
from src.utils.currency import CurrencyCalculator

from .models import Subscription, User


class UserRepository:
    """User repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> User:
        """Create or update user."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            user.last_seen = datetime.utcnow()
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_seen=datetime.utcnow(),
            )
            self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, telegram_id: int) -> User | None:
        """Get user by telegram_id."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_seen(self, telegram_id: int) -> None:
        """Update user's last seen time."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_seen=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def count_active_24h(self) -> int:
        """Count users active in last 24 hours."""
        threshold = datetime.utcnow() - timedelta(hours=24)
        stmt = select(func.count(User.telegram_id)).where(User.last_seen >= threshold)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_total(self) -> int:
        """Count total users."""
        stmt = select(func.count(User.telegram_id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class SubscriptionRepository:
    """Subscription repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, telegram_id: int, data: dict[str, Any]) -> Subscription:
        """Create subscription."""
        subscription = Subscription(telegram_id=telegram_id, **data)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: int) -> Subscription | None:
        """Get subscription by ID."""
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, subscription_id: int) -> Subscription:
        """
        Get subscription by ID or raise NotFoundException.

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
        """Get all active subscriptions for user."""
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
        """Update subscription."""
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
        """Mark subscription as inactive."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False

        subscription.is_active = False
        # updated_at is automatically set by SQLAlchemy onupdate
        await self.session.commit()
        return True

    async def get_pending_notifications(self, target_date: date) -> list[Subscription]:
        """Get subscriptions requiring notification."""
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
        """Advance next_payment by period_days."""
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
        """Advance all past payments to next period."""
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

    async def count_total(self) -> int:
        """Count total active subscriptions."""
        stmt = select(func.count(Subscription.id)).where(Subscription.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_total_monthly_amount_rub(self) -> float:
        """Get total monthly amount in RUB (simplified)."""
        # Simplified: only count RUB subscriptions, convert to monthly
        stmt = select(Subscription).where(
            and_(
                Subscription.is_active == True,
                Subscription.currency == "RUB",
            )
        )
        result = await self.session.execute(stmt)
        subscriptions = result.scalars().all()

        calculator = CurrencyCalculator()
        total = 0.0
        for sub in subscriptions:
            # Use centralized calculation logic
            monthly = calculator.to_monthly_equivalent(sub.amount, sub.period_days)
            total += monthly

        return total
