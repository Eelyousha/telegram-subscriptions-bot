"""User repository."""
from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UserRepository:
    """User repository for CRUD operations and queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> User:
        """Create or update user.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name

        Returns:
            User object
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            user.last_seen = datetime.utcnow()
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_seen=datetime.utcnow(),
            )
            self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, telegram_id: int) -> User | None:
        """Get user by telegram_id.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object or None if not found
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_seen(self, telegram_id: int) -> None:
        """Update user's last seen time.

        Args:
            telegram_id: Telegram user ID
        """
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_seen=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def count_active_24h(self) -> int:
        """Count users active in last 24 hours.

        Returns:
            Number of active users
        """
        threshold = datetime.utcnow() - timedelta(hours=24)
        stmt = select(func.count(User.telegram_id)).where(User.last_seen >= threshold)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_total(self) -> int:
        """Count total users.

        Returns:
            Total number of users
        """
        stmt = select(func.count(User.telegram_id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
