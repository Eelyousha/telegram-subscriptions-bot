"""Test currency utilities."""
import pytest

from src.utils.converters import StaticCurrencyConverter
from src.utils.currency import Currency, CurrencyCalculator


class TestCurrencyCalculator:
    """Test CurrencyCalculator."""

    def test_weekly_to_monthly(self):
        """Test weekly subscription conversion."""
        result = CurrencyCalculator.to_monthly_equivalent(100, 7)
        assert result == pytest.approx(433.0, rel=0.01)

    def test_yearly_to_monthly(self):
        """Test yearly subscription conversion."""
        result = CurrencyCalculator.to_monthly_equivalent(1200, 365)
        assert result == pytest.approx(100.0, rel=0.01)

    def test_monthly_to_monthly(self):
        """Test monthly subscription conversion."""
        result = CurrencyCalculator.to_monthly_equivalent(500, 30)
        assert result == pytest.approx(500.0, rel=0.01)

    def test_custom_period_to_monthly(self):
        """Test custom period conversion."""
        result = CurrencyCalculator.to_monthly_equivalent(200, 15)
        # 200 * (30 / 15) = 400
        assert result == pytest.approx(400.0, rel=0.01)


class TestStaticCurrencyConverter:
    """Test StaticCurrencyConverter."""

    def test_convert_rub_to_rub(self):
        """Test RUB to RUB conversion."""
        result = StaticCurrencyConverter.to_rub(100, Currency.RUB)
        assert result == 100.0

    def test_convert_usd_to_rub(self):
        """Test USD to RUB conversion."""
        result = StaticCurrencyConverter.to_rub(100, Currency.USD)
        assert result == 9000.0  # 100 * 90

    def test_convert_eur_to_rub(self):
        """Test EUR to RUB conversion."""
        result = StaticCurrencyConverter.to_rub(100, Currency.EUR)
        assert result == 10000.0  # 100 * 100

    def test_convert_with_string(self):
        """Test conversion with string currency."""
        result = StaticCurrencyConverter.to_rub(100, "USD")
        assert result == 9000.0

    def test_convert_between_currencies(self):
        """Test conversion between two currencies."""
        result = StaticCurrencyConverter.convert(100, Currency.USD, Currency.EUR)
        # 100 USD = 9000 RUB, 9000 RUB = 90 EUR
        assert result == pytest.approx(90.0, rel=0.01)
