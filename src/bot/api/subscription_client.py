"""Subscription API client."""
import httpx

from src.core.config import settings


class SubscriptionAPIClient:
    """HTTP client for subscription-related API operations."""

    def __init__(self, base_url: str | None = None):
        """Initialize subscription API client.

        Args:
            base_url: Base URL for API. If None, uses settings.api_url
        """
        self.base_url = base_url or settings.api_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def get_subscriptions(self, telegram_id: int) -> list[dict]:
        """Get user's subscriptions.

        Args:
            telegram_id: Telegram user ID

        Returns:
            List of subscription data

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        response = await self.client.get(f"/users/{telegram_id}/subscriptions")
        response.raise_for_status()
        return response.json()

    async def create_subscription(self, telegram_id: int, data: dict) -> dict:
        """Create a subscription.

        Args:
            telegram_id: Telegram user ID
            data: Subscription data

        Returns:
            Created subscription data

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        response = await self.client.post(
            f"/users/{telegram_id}/subscriptions", json=data
        )
        response.raise_for_status()
        return response.json()

    async def update_subscription(self, subscription_id: int, data: dict) -> dict:
        """Update a subscription.

        Args:
            subscription_id: Subscription ID
            data: Updated subscription data

        Returns:
            Updated subscription data

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        response = await self.client.patch(
            f"/subscriptions/{subscription_id}", json=data
        )
        response.raise_for_status()
        return response.json()

    async def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        response = await self.client.delete(f"/subscriptions/{subscription_id}")
        response.raise_for_status()
        return True

    async def get_stats(self, telegram_id: int) -> dict:
        """Get user statistics.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User statistics data

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        response = await self.client.get(f"/users/{telegram_id}/stats")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
