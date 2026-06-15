import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError
from app.core.exceptions import UnauthorizedError
from app.core.security import create_token
from app.core.security import decode_token
from app.core.security import hash_password
from app.core.security import verify_password
from app.models.user import User
from app.models.user import UserRole
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def _handle_integrity_error(self, error: IntegrityError) -> None:
        await self.session.rollback()
        raise ConflictError(
            "Нарушение целостности данных при работе с пользователями."
        ) from error

    async def register(self, data: UserCreate) -> User:
        existing = await self.repo.get_by_username(data.username)
        if existing:
            raise ConflictError("Пользователь с таким именем уже существует.")
        try:
            user = await self.repo.create(
                username=data.username,
                password_hash=hash_password(data.password),
                role=data.role,
            )
            await self.session.commit()
            return user
        except IntegrityError as e:
            await self._handle_integrity_error(e)

    async def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        user: User | None = None,
    ) -> TokenResponse:
        """
        if user is None:
            ... обычная аутентификация по логину и паролю ...
        (вызов из метода регистрации)
        упрощенная аутентификация - без лишнего запроса к БД.
        """
        if user is None:
            user = await self.repo.get_by_username(username)

            if not user or not verify_password(password, user.password_hash):
                raise UnauthorizedError("Неверное имя пользователя или пароль.")

        access_token = create_token(data={"sub": str(user.id)}, token_type="access")
        refresh_token = create_token(data={"sub": str(user.id)}, token_type="refresh")
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            token_type = payload.get("type")
            if token_type != "refresh":
                raise UnauthorizedError("Токен не является refresh-токеном.")
            # Не через payload["sub"], чтобы не было KeyError,
            # если в payload нет таких пар ключ / значение:
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedError("Токен не содержит идентификатор пользователя.")
            user = await self.repo.get_by_id(int(user_id))
            if not user:
                # Здесь вручную возбуждаем UnauthorizedError, так как в
                # других местах отсутствие чего-либо - это NotFoundError:
                raise UnauthorizedError("Пользователь не найден.")
            new_access = create_token(data={"sub": user_id}, token_type="access")
            new_refresh = create_token(data={"sub": user_id}, token_type="refresh")

            return TokenResponse(access_token=new_access, refresh_token=new_refresh)

        except (ValueError, jwt.InvalidTokenError):
            raise UnauthorizedError("Недействительный refresh-токен.")

    async def create_admin_if_not_exists(self):
        """
        Создает начального пользователя-администратора,
        если его еще нет.
        """
        username = settings.ADMIN_USERNAME
        password = settings.ADMIN_PASSWORD.get_secret_value()
        role = UserRole.ADMIN

        admin_data = UserCreate(
            username=username,
            password=password,
            role=role,
        )
        # Если начальный админ уже в БД - то перехватываем ошибку, чтобы
        # бекенд не падал (так как вызов не через FastAPI - то перехватчики
        # исключений не сработают), try/except вместо exist запроса к БД -
        # большая надежность, защита от состояния гонки:
        try:
            await self.register(admin_data)
            print(f"Начальный администратор {username} Добавлен в БД.")
        except ConflictError:
            print("Начальный администратор уже в БД")
