"""Test formatter utilities."""
from datetime import date, timedelta

import pytest

from src.utils.formatters import DateFormatter, PeriodFormatter, AmountFormatter


class TestPeriodFormatter:
    """Test PeriodFormatter."""

    def test_format_weekly_nominative(self):
        """Test weekly period in nominative case."""
        result = PeriodFormatter.format(7)
        assert result == "неделя"

    def test_format_weekly_accusative(self):
        """Test weekly period in accusative case."""
        result = PeriodFormatter.format(7, case="accusative")
        assert result == "неделю"

    def test_format_monthly(self):
        """Test monthly period."""
        result = PeriodFormatter.format(30)
        assert result == "месяц"

    def test_format_yearly(self):
        """Test yearly period."""
        result = PeriodFormatter.format(365)
        assert result == "год"

    def test_format_custom_period(self):
        """Test custom period."""
        result = PeriodFormatter.format(90)
        assert result == "90 дн."

    def test_format_with_preposition(self):
        """Test period with preposition."""
        result = PeriodFormatter.format_with_preposition(7)
        assert result == "/неделю"


class TestDateFormatter:
    """Test DateFormatter."""

    def test_format_russian(self):
        """Test Russian date format."""
        test_date = date(2026, 1, 15)
        result = DateFormatter.format_russian(test_date)
        assert result == "15.01.2026"

    def test_days_until_future(self):
        """Test days until future date."""
        future_date = date.today() + timedelta(days=5)
        result = DateFormatter.days_until(future_date)
        assert result == 5

    def test_days_until_past(self):
        """Test days until past date."""
        past_date = date.today() - timedelta(days=3)
        result = DateFormatter.days_until(past_date)
        assert result == -3

    def test_format_days_left_today(self):
        """Test format for today."""
        result = DateFormatter.format_days_left(date.today())
        assert result == "сегодня"

    def test_format_days_left_tomorrow(self):
        """Test format for tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        result = DateFormatter.format_days_left(tomorrow)
        assert result == "завтра"

    def test_format_days_left_future(self):
        """Test format for future date."""
        future = date.today() + timedelta(days=5)
        result = DateFormatter.format_days_left(future)
        assert result == "через 5 дн."


class TestAmountFormatter:
    """Test AmountFormatter."""

    def test_format_amount_with_currency(self):
        """Test amount formatting with currency."""
        result = AmountFormatter.format_amount(1500.50, "RUB")
        assert result == "1500.50 RUB"

    def test_format_amount_compact_whole(self):
        """Test compact format for whole numbers."""
        result = AmountFormatter.format_amount_compact(1500.00)
        assert result == "1500"

    def test_format_amount_compact_decimal(self):
        """Test compact format for decimals."""
        result = AmountFormatter.format_amount_compact(1500.50)
        assert result == "1500.50"
