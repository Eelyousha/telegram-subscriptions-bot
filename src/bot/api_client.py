"""API client for bot."""
import httpx

from src.core.config import settings


class APIClient:
    """HTTP client for communicating with API."""

    def __init__(self):
        self.base_url = settings.api_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def create_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> dict:
        """Create or update user."""
        response = await self.client.post(
            "/users",
            json={
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_subscriptions(self, telegram_id: int) -> list[dict]:
        """Get user's subscriptions."""
        response = await self.client.get(f"/users/{telegram_id}/subscriptions")
        response.raise_for_status()
        return response.json()

    async def create_subscription(self, telegram_id: int, data: dict) -> dict:
        """Create a subscription."""
        response = await self.client.post(
            f"/users/{telegram_id}/subscriptions", json=data
        )
        response.raise_for_status()
        return response.json()

    async def update_subscription(self, subscription_id: int, data: dict) -> dict:
        """Update a subscription."""
        response = await self.client.patch(
            f"/subscriptions/{subscription_id}", json=data
        )
        response.raise_for_status()
        return response.json()

    async def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        response = await self.client.delete(f"/subscriptions/{subscription_id}")
        response.raise_for_status()
        return True

    async def get_stats(self, telegram_id: int) -> dict:
        """Get user statistics."""
        response = await self.client.get(f"/users/{telegram_id}/stats")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
