"""User API client."""
import httpx

from src.core.config import settings


class UserAPIClient:
    """HTTP client for user-related API operations."""

    def __init__(self, base_url: str | None = None):
        """Initialize user API client.

        Args:
            base_url: Base URL for API. If None, uses settings.api_url
        """
        self.base_url = base_url or settings.api_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def create_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> dict:
        """Create or update user.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name

        Returns:
            User data from API

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
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

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
