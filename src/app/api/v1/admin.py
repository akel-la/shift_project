from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import ForbiddenError
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.user import UserRole
from app.schemas.user import TokenResponse
from app.schemas.user import UserCreate
from app.services.auth import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def create_admin(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    data: UserCreate,
    ):
    """
    Создание нового администратора.
    Только существующий администратор может выполнить этот запрос.
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(
            "Зарегистрировать нового администратора могут только другие администраторы."
        )
    if data.role != UserRole.ADMIN:
        raise ForbiddenError(
            "Этот URL предназначен только для регистрации администраторов."
        )

    auth_service = AuthService(session)
    new_admin = await auth_service.register(data)
    return await auth_service.authenticate(user=new_admin)
