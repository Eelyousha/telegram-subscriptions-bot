"""API client protocols."""
from typing import Protocol


class UserAPIClientProtocol(Protocol):
    """Protocol for User API client."""

    async def create_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> dict:
        """Create or update user."""
        ...


class SubscriptionAPIClientProtocol(Protocol):
    """Protocol for Subscription API client."""

    async def get_subscriptions(self, telegram_id: int) -> list[dict]:
        """Get user's subscriptions."""
        ...

    async def create_subscription(self, telegram_id: int, data: dict) -> dict:
        """Create a subscription."""
        ...

    async def update_subscription(self, subscription_id: int, data: dict) -> dict:
        """Update a subscription."""
        ...

    async def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        ...

    async def get_stats(self, telegram_id: int) -> dict:
        """Get user statistics."""
        ...
