from pydantic import Field

from app.core.schema import BaseSchema
from app.models.user import UserRole


class UserCreate(BaseSchema):
    """
    Тело запроса для регистрации пользователя (сотрудника или администратора).
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    role: UserRole = UserRole.EMPLOYEE


class UserUpdate(BaseSchema):
    """
    Тело запроса для обновления профиля.
    Все поля необязательные – клиент передаёт только то, что хочет изменить.
    Роль можно указать, но изменить её сможет только администратор (проверка в сервисе).
    """

    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=6, max_length=50)
    role: UserRole | None = None


class UserPrivate(BaseSchema):
    """
    Приватная информация о пользователе (для владельца профиля).
    """

    id: int = Field(gt=0)
    username: str
    role: UserRole


class TokenResponse(BaseSchema):
    """
    Ответ с парой JWT-токенов.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    """
    Тело запроса для обновления токенов.
    """

    refresh_token: str
