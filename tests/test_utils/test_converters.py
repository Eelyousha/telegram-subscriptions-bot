"""Test currency converter strategies."""
import pytest

from src.utils.converters import DynamicCurrencyConverter, StaticCurrencyConverter
from src.utils.currency import Currency


class TestStaticCurrencyConverter:
    """Test StaticCurrencyConverter strategy."""

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


class TestDynamicCurrencyConverter:
    """Test DynamicCurrencyConverter strategy."""

    def test_default_rates(self):
        """Test converter with default rates."""
        converter = DynamicCurrencyConverter()
        result = converter.to_rub(100, Currency.USD)
        assert result == 9000.0

    def test_custom_rates(self):
        """Test converter with custom rates."""
        custom_rates = {
            Currency.RUB: 1.0,
            Currency.USD: 95.0,  # Different rate
            Currency.EUR: 105.0,
        }
        converter = DynamicCurrencyConverter(rates=custom_rates)
        result = converter.to_rub(100, Currency.USD)
        assert result == 9500.0  # 100 * 95

    def test_update_rates(self):
        """Test updating rates dynamically."""
        converter = DynamicCurrencyConverter()

        # Initial rate
        result1 = converter.to_rub(100, Currency.USD)
        assert result1 == 9000.0

        # Update rates
        new_rates = {
            Currency.RUB: 1.0,
            Currency.USD: 85.0,  # New rate
            Currency.EUR: 95.0,
        }
        converter.update_rates(new_rates)

        # Check new rate is applied
        result2 = converter.to_rub(100, Currency.USD)
        assert result2 == 8500.0  # 100 * 85

    def test_convert_between_currencies(self):
        """Test conversion between two currencies."""
        converter = DynamicCurrencyConverter()
        result = converter.convert(100, Currency.USD, Currency.EUR)
        # 100 USD = 9000 RUB, 9000 RUB = 90 EUR
        assert result == pytest.approx(90.0, rel=0.01)

    def test_convert_with_string_currency(self):
        """Test conversion with string currency types."""
        converter = DynamicCurrencyConverter()
        result = converter.to_rub(100, "USD")
        assert result == 9000.0
