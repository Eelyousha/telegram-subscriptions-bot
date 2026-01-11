"""User routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import schemas
from src.api.dependencies import get_db, get_user_repository
from src.api.exceptions import NotFoundException
from src.db.repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.User)
async def create_or_update_user(
    user_data: schemas.UserCreate,
    session: AsyncSession = Depends(get_db),
) -> schemas.User:
    """Create or update user."""
    repo = UserRepository(session)
    user = await repo.upsert(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        first_name=user_data.first_name,
    )
    return schemas.User.model_validate(user)


@router.get("/{telegram_id}", response_model=schemas.User)
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
) -> schemas.User:
    """Get user by telegram_id."""
    repo = UserRepository(session)
    user = await repo.get(telegram_id)
    if not user:
        raise NotFoundException("User not found")
    return schemas.User.model_validate(user)
