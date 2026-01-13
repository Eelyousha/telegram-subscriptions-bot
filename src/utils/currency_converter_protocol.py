"""Currency converter protocol."""
from typing import Protocol

from src.utils.currency import Currency


class CurrencyConverterProtocol(Protocol):
    """Protocol for currency conversion strategies."""

    def to_rub(self, amount: float, from_currency: Currency | str) -> float:
        """Convert amount to RUB.

        Args:
            amount: Amount to convert
            from_currency: Source currency

        Returns:
            Amount in RUB
        """
        ...

    def convert(
        self, amount: float, from_currency: Currency | str, to_currency: Currency | str
    ) -> float:
        """Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        ...
