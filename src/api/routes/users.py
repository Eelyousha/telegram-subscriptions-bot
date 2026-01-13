"""User routes."""
from fastapi import APIRouter, Depends

from src.api import schemas
from src.api.dependencies import get_user_service
from src.api.exceptions import ErrorMessages, NotFoundException
from src.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.User)
async def create_or_update_user(
    user_data: schemas.UserCreate,
    service: UserService = Depends(get_user_service),
) -> schemas.User:
    """Create or update user."""
    user = await service.create_or_update_user(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        first_name=user_data.first_name,
    )
    return schemas.User.model_validate(user)


@router.get("/{telegram_id}", response_model=schemas.User)
async def get_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
) -> schemas.User:
    """Get user by telegram_id."""
    user = await service.get_user(telegram_id)
    if not user:
        raise NotFoundException(ErrorMessages.USER_NOT_FOUND)
    return schemas.User.model_validate(user)
