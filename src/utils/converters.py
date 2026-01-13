"""Currency converter strategies implementing Strategy Pattern."""
from src.utils.currency import Currency


class StaticCurrencyConverter:
    """
    Static currency converter with fixed exchange rates.

    This strategy uses predefined static rates and is suitable for
    testing or when real-time rates are not required.
    """

    # Exchange rates to RUB (as of 2026-01)
    RATES = {
        Currency.RUB: 1.0,
        Currency.USD: 90.0,
        Currency.EUR: 100.0,
    }

    @classmethod
    def to_rub(cls, amount: float, from_currency: Currency | str) -> float:
        """Convert amount to RUB using static rates.

        Args:
            amount: Amount to convert
            from_currency: Source currency

        Returns:
            Amount in RUB

        Examples:
            >>> StaticCurrencyConverter.to_rub(100, Currency.USD)
            9000.0
            >>> StaticCurrencyConverter.to_rub(100, "RUB")
            100.0
        """
        if isinstance(from_currency, str):
            from_currency = Currency(from_currency)
        return amount * cls.RATES[from_currency]

    @classmethod
    def convert(
        cls, amount: float, from_currency: Currency | str, to_currency: Currency | str
    ) -> float:
        """Convert between any two currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount

        Examples:
            >>> StaticCurrencyConverter.convert(100, Currency.USD, Currency.EUR)
            90.0
        """
        if isinstance(from_currency, str):
            from_currency = Currency(from_currency)
        if isinstance(to_currency, str):
            to_currency = Currency(to_currency)

        # Convert to RUB first, then to target currency
        amount_in_rub = amount * cls.RATES[from_currency]
        return amount_in_rub / cls.RATES[to_currency]


class DynamicCurrencyConverter:
    """
    Dynamic currency converter that could fetch real-time rates.

    This strategy demonstrates the Strategy Pattern. In production,
    this would fetch rates from an external API (e.g., CBR, ECB).
    For now, it uses the same static rates as a placeholder.
    """

    def __init__(self, rates: dict[Currency, float] | None = None):
        """Initialize converter with custom rates.

        Args:
            rates: Custom exchange rates to RUB. If None, uses default static rates.
        """
        self.rates = rates or {
            Currency.RUB: 1.0,
            Currency.USD: 90.0,
            Currency.EUR: 100.0,
        }

    def update_rates(self, rates: dict[Currency, float]) -> None:
        """Update exchange rates.

        Args:
            rates: New exchange rates to RUB
        """
        self.rates = rates

    def to_rub(self, amount: float, from_currency: Currency | str) -> float:
        """Convert amount to RUB using current rates.

        Args:
            amount: Amount to convert
            from_currency: Source currency

        Returns:
            Amount in RUB
        """
        if isinstance(from_currency, str):
            from_currency = Currency(from_currency)
        return amount * self.rates[from_currency]

    def convert(
        self, amount: float, from_currency: Currency | str, to_currency: Currency | str
    ) -> float:
        """Convert between any two currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        if isinstance(from_currency, str):
            from_currency = Currency(from_currency)
        if isinstance(to_currency, str):
            to_currency = Currency(to_currency)

        # Convert to RUB first, then to target currency
        amount_in_rub = amount * self.rates[from_currency]
        return amount_in_rub / self.rates[to_currency]


# Default converter instance for backward compatibility
DEFAULT_CONVERTER = StaticCurrencyConverter()
