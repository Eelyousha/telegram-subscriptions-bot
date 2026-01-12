"""Currency and period conversion utilities."""
from enum import Enum


class Currency(str, Enum):
    """Supported currencies."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class CurrencyCalculator:
    """Utility for currency and period calculations."""

    @staticmethod
    def to_monthly_equivalent(amount: float, period_days: int) -> float:
        """
        Convert subscription amount to monthly equivalent.

        Args:
            amount: Subscription amount
            period_days: Period in days (7, 30, 365, or custom)

        Returns:
            Monthly equivalent amount

        Examples:
            >>> CurrencyCalculator.to_monthly_equivalent(100, 7)
            433.0
            >>> CurrencyCalculator.to_monthly_equivalent(1200, 365)
            100.0
            >>> CurrencyCalculator.to_monthly_equivalent(500, 30)
            500.0
        """
        if period_days == 7:
            # Weekly: 4.33 weeks per month
            return amount * 4.33
        elif period_days == 365:
            # Yearly: divide by 12 months
            return amount / 12
        else:
            # Custom: proportional to 30 days
            return amount * (30 / period_days)
