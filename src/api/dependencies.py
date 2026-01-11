"""FastAPI dependencies."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import AsyncSessionLocal
from src.db.repository import SubscriptionRepository, UserRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_repository(session: AsyncSession) -> UserRepository:
    """Get user repository."""
    return UserRepository(session)


async def get_subscription_repository(session: AsyncSession) -> SubscriptionRepository:
    """Get subscription repository."""
    return SubscriptionRepository(session)
