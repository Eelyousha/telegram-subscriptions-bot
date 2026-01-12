"""Subscription business logic service."""
from datetime import date
from typing import Any

from src.db.models import Subscription
from src.db.repositories import SubscriptionRepository
from src.utils.currency import CurrencyCalculator


class SubscriptionService:
    """Service for subscription business logic."""

    def __init__(self, repository: SubscriptionRepository):
        """
        Initialize service.

        Args:
            repository: Subscription repository
        """
        self.repository = repository
        self.calculator = CurrencyCalculator()

    async def create_subscription(
        self,
        telegram_id: int,
        data: dict[str, Any],
    ) -> Subscription:
        """
        Create a new subscription.

        Args:
            telegram_id: User's Telegram ID
            data: Subscription data

        Returns:
            Created subscription
        """
        return await self.repository.create(telegram_id=telegram_id, data=data)

    async def get_subscription(self, subscription_id: int) -> Subscription:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription object

        Raises:
            NotFoundException: If subscription not found
        """
        return await self.repository.get_by_id_or_raise(subscription_id)

    async def get_user_subscriptions(self, telegram_id: int) -> list[Subscription]:
        """
        Get all subscriptions for user.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            List of subscriptions
        """
        return await self.repository.get_all_by_user(telegram_id)

    async def update_subscription(
        self,
        subscription_id: int,
        data: dict[str, Any],
    ) -> Subscription:
        """
        Update subscription.

        Args:
            subscription_id: Subscription ID
            data: Update data

        Returns:
            Updated subscription

        Raises:
            NotFoundException: If subscription not found
        """
        subscription = await self.repository.update(subscription_id, data)
        if not subscription:
            return await self.repository.get_by_id_or_raise(subscription_id)
        return subscription

    async def delete_subscription(self, subscription_id: int) -> bool:
        """
        Soft delete subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: If subscription not found
        """
        success = await self.repository.soft_delete(subscription_id)
        if not success:
            # Will raise NotFoundException
            await self.repository.get_by_id_or_raise(subscription_id)
        return success

    async def calculate_user_stats(self, telegram_id: int) -> dict[str, Any]:
        """
        Calculate comprehensive user statistics.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Dictionary with statistics:
                - total_subscriptions: Total number of active subscriptions
                - total_monthly_rub: Total monthly amount in RUB
                - by_currency: List of stats per currency
                - upcoming_payments: List of upcoming payments (next 30 days, max 5)
        """
        subscriptions = await self.repository.get_all_by_user(telegram_id)

        # Calculate total subscriptions
        total_subscriptions = len(subscriptions)

        # Group by currency and calculate monthly amounts
        currency_stats: dict[str, dict[str, Any]] = {}
        for sub in subscriptions:
            if sub.currency not in currency_stats:
                currency_stats[sub.currency] = {"total": 0.0, "count": 0}

            # Convert to monthly equivalent
            monthly = self.calculator.to_monthly_equivalent(sub.amount, sub.period_days)
            currency_stats[sub.currency]["total"] += monthly
            currency_stats[sub.currency]["count"] += 1

        # Format currency stats
        by_currency = [
            {
                "currency": curr,
                "total_monthly": stats["total"],
                "count": stats["count"],
            }
            for curr, stats in currency_stats.items()
        ]

        # Get upcoming payments (next 30 days, max 5)
        upcoming_payments = self._get_upcoming_payments(subscriptions, days=30, limit=5)

        # Total monthly in RUB (simplified, no conversion for now)
        total_monthly_rub = currency_stats.get("RUB", {}).get("total", 0.0)

        return {
            "total_subscriptions": total_subscriptions,
            "total_monthly_rub": total_monthly_rub,
            "by_currency": by_currency,
            "upcoming_payments": upcoming_payments,
        }

    def _get_upcoming_payments(
        self,
        subscriptions: list[Subscription],
        days: int = 30,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get upcoming payments within specified days.

        Args:
            subscriptions: List of subscriptions
            days: Number of days to look ahead
            limit: Maximum number of payments to return

        Returns:
            List of upcoming payment dictionaries
        """
        today = date.today()

        # Filter payments within timeframe
        upcoming = [
            {
                "subscription_id": sub.id,
                "name": sub.name,
                "amount": sub.amount,
                "currency": sub.currency,
                "date": sub.next_payment,
                "days_left": (sub.next_payment - today).days,
            }
            for sub in subscriptions
            if (sub.next_payment - today).days <= days
        ]

        # Sort by date and limit
        upcoming.sort(key=lambda x: x["date"])
        return upcoming[:limit]

    async def get_monthly_total_rub(self) -> float:
        """
        Get total monthly amount in RUB across all users.

        Uses the centralized calculation logic.

        Returns:
            Total monthly amount in RUB
        """
        return await self.repository.get_total_monthly_amount_rub()

    async def advance_past_payments(self) -> int:
        """
        Advance all past payment dates to future.

        Returns:
            Number of subscriptions updated
        """
        return await self.repository.advance_past_payments()
