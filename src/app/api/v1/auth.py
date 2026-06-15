from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import ForbiddenError
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.user import UserRole
from app.schemas.user import RefreshTokenRequest
from app.schemas.user import TokenResponse
from app.schemas.user import UserCreate
from app.schemas.user import UserPrivate
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    data: UserCreate,
):
    """
    Регистрация обычного сотрудника.
    Запрещено создавать учётную запись с ролью администратора.
    """
    if data.role != UserRole.EMPLOYEE:
        raise ForbiddenError("Вы можете зарегистрироваться только как сотрудник.")
    data.role = UserRole.EMPLOYEE  # принудительно, даже если обошли проверку

    auth_service = AuthService(session)
    new_user = await auth_service.register(data)
    return await auth_service.authenticate(user=new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Аутентификация по логину и паролю. Возвращает access и refresh токены."""
    auth_service = AuthService(session)
    return await auth_service.authenticate(
        username=form_data.username,
        password=form_data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    data: RefreshTokenRequest,
):
    """Обновление пары токенов по refresh-токену."""
    auth_service = AuthService(session)
    return await auth_service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserPrivate)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Возвращает профиль текущего пользователя."""
    return current_user
