"""Formatting utilities for display."""
from datetime import date
from typing import Literal


class PeriodFormatter:
    """Formatter for subscription periods."""

    # Period names in different grammatical cases
    PERIOD_NAMES = {
        "nominative": {  # именительный падеж (что?)
            7: "неделя",
            30: "месяц",
            365: "год",
        },
        "accusative": {  # винительный падеж (на сколько?)
            7: "неделю",
            30: "месяц",
            365: "год",
        },
    }

    @classmethod
    def format(
        cls,
        period_days: int,
        case: Literal["nominative", "accusative"] = "nominative",
    ) -> str:
        """
        Format period days to human-readable text.

        Args:
            period_days: Number of days in period (7, 30, 365, or custom)
            case: Grammatical case ("nominative" or "accusative")

        Returns:
            Human-readable period text

        Examples:
            >>> PeriodFormatter.format(7)
            'неделя'
            >>> PeriodFormatter.format(7, case="accusative")
            'неделю'
            >>> PeriodFormatter.format(90)
            '90 дн.'
        """
        period_map = cls.PERIOD_NAMES.get(case, cls.PERIOD_NAMES["nominative"])
        return period_map.get(period_days, f"{period_days} дн.")

    @classmethod
    def format_with_preposition(cls, period_days: int) -> str:
        """
        Format period with preposition (per period).

        Args:
            period_days: Number of days in period

        Returns:
            Formatted text with preposition

        Examples:
            >>> PeriodFormatter.format_with_preposition(7)
            '/неделю'
            >>> PeriodFormatter.format_with_preposition(30)
            '/месяц'
            >>> PeriodFormatter.format_with_preposition(90)
            '/90 дн.'
        """
        period_text = cls.format(period_days, case="accusative")
        return f"/{period_text}"


class DateFormatter:
    """Formatter for dates."""

    @staticmethod
    def format_russian(date_obj: date) -> str:
        """
        Format date in Russian format (DD.MM.YYYY).

        Args:
            date_obj: Date to format

        Returns:
            Formatted date string

        Examples:
            >>> from datetime import date
            >>> DateFormatter.format_russian(date(2026, 1, 15))
            '15.01.2026'
        """
        return date_obj.strftime("%d.%m.%Y")

    @staticmethod
    def days_until(target_date: date) -> int:
        """
        Calculate days until target date.

        Args:
            target_date: Target date

        Returns:
            Number of days (negative if in past)

        Examples:
            >>> from datetime import date, timedelta
            >>> future = date.today() + timedelta(days=5)
            >>> DateFormatter.days_until(future)
            5
        """
        return (target_date - date.today()).days

    @classmethod
    def format_days_left(cls, target_date: date) -> str:
        """
        Format days left until date in human-readable form.

        Args:
            target_date: Target date

        Returns:
            Human-readable text

        Examples:
            >>> from datetime import date, timedelta
            >>> today = date.today()
            >>> DateFormatter.format_days_left(today)
            'сегодня'
            >>> tomorrow = today + timedelta(days=1)
            >>> DateFormatter.format_days_left(tomorrow)
            'завтра'
        """
        days = cls.days_until(target_date)

        if days == 0:
            return "сегодня"
        elif days == 1:
            return "завтра"
        elif days == 2:
            return "послезавтра"
        elif days < 0:
            return f"{abs(days)} дн. назад"
        else:
            return f"через {days} дн."


class AmountFormatter:
    """Formatter for monetary amounts."""

    @staticmethod
    def format_amount(amount: float, currency: str) -> str:
        """
        Format amount with currency.

        Args:
            amount: Amount to format
            currency: Currency code

        Returns:
            Formatted string

        Examples:
            >>> AmountFormatter.format_amount(1500.50, "RUB")
            '1500.50 RUB'
            >>> AmountFormatter.format_amount(100, "USD")
            '100.00 USD'
        """
        return f"{amount:.2f} {currency}"

    @staticmethod
    def format_amount_compact(amount: float) -> str:
        """
        Format amount in compact form (rounds to integer if whole number).

        Args:
            amount: Amount to format

        Returns:
            Formatted string

        Examples:
            >>> AmountFormatter.format_amount_compact(1500.00)
            '1500'
            >>> AmountFormatter.format_amount_compact(1500.50)
            '1500.50'
        """
        if amount == int(amount):
            return str(int(amount))
        return f"{amount:.2f}"
