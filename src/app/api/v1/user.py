from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserPrivate
from app.schemas.user import UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPrivate)
async def get_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = UserService(session)
    return await service.get(current_user, user_id)


@router.put("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = UserService(session)
    return await service.update(
        current_user, user_id, **data.model_dump(exclude_unset=True)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = UserService(session)
    await service.delete(current_user, user_id)
