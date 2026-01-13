"""FastAPI dependencies."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import AsyncSessionLocal
from src.db.repositories import SubscriptionRepository, UserRepository
from src.services import SubscriptionService, UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository."""
    return UserRepository(session)


async def get_subscription_repository(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    """Get subscription repository."""
    return SubscriptionRepository(session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Get user service."""
    return UserService(repository)


async def get_subscription_service(
    repository: SubscriptionRepository = Depends(get_subscription_repository),
) -> SubscriptionService:
    """Get subscription service."""
    return SubscriptionService(repository)
