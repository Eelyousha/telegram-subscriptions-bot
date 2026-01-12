"""Subscription analytics repository."""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Subscription
from src.utils.currency import CurrencyCalculator


class SubscriptionAnalyticsRepository:
    """Subscription repository for analytics and statistics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_total(self) -> int:
        """Count total active subscriptions.

        Returns:
            Number of active subscriptions
        """
        stmt = select(func.count(Subscription.id)).where(Subscription.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_total_monthly_amount_rub(self) -> float:
        """Get total monthly amount in RUB (simplified).

        This is a simplified calculation that only counts RUB subscriptions
        and converts them to monthly equivalents.

        Returns:
            Total monthly amount in RUB
        """
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
