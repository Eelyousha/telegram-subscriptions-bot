"""User business logic service."""
from src.db.models import User
from src.db.repositories import UserRepository


class UserService:
    """Service for user business logic."""

    def __init__(self, repository: UserRepository):
        """
        Initialize service.

        Args:
            repository: User repository
        """
        self.repository = repository

    async def create_or_update_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        """
        Create or update user.

        Args:
            telegram_id: User's Telegram ID
            username: Telegram username
            first_name: User's first name

        Returns:
            User object
        """
        return await self.repository.upsert(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )

    async def get_user(self, telegram_id: int) -> User | None:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            User object or None
        """
        return await self.repository.get(telegram_id)

    async def update_last_seen(self, telegram_id: int) -> None:
        """
        Update user's last seen timestamp.

        Args:
            telegram_id: User's Telegram ID
        """
        await self.repository.update_last_seen(telegram_id)

    async def count_active_users_24h(self) -> int:
        """
        Count users active in last 24 hours.

        Returns:
            Number of active users
        """
        return await self.repository.count_active_24h()

    async def count_total_users(self) -> int:
        """
        Count total number of users.

        Returns:
            Total user count
        """
        return await self.repository.count_total()
