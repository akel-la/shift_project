from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.exceptions import ForbiddenError
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.models.user import UserRole
from app.repositories.user import UserRepository


# Внутри нет create, так как этим занимается AuthService,
# напрямую обращаясь к UserRepository.
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def _get_or_exc(self, user_id: int, *, load_bookings: bool = False) -> User:
        user = await self.repo.get_by_id(user_id, load_bookings=load_bookings)
        if not user:
            raise NotFoundError(f"Пользователь с id = {user_id} не найден.")
        return user

    async def _handle_integrity_error(self, error: IntegrityError) -> None:
        await self.session.rollback()
        raise ConflictError(
            "Нарушение целостности данных при работе с пользователями."
        ) from error

    def _check_permission(self, current_user: User, target_user_id: int):
        if current_user.role != UserRole.ADMIN and current_user.id != target_user_id:
            raise ForbiddenError("Вы можете работать только со своим профилем.")

    async def get_by_id(self, user_id: int, *, load_bookings: bool = False) -> User:
        """
        Возвращает информацию о пользователе (не проверяем права).
        """
        return await self._get_or_exc(user_id, load_bookings=load_bookings)

    async def get(
        self,
        current_user: User,
        target_user_id: int,
        *,
        load_bookings: bool = False,
    ) -> User:
        """
        Возвращает информацию о пользователе:
        1) Для обычных пользователей - только о самом себе.
        2) Для администраторов - о любых пользователях.
        """
        self._check_permission(current_user, target_user_id)
        return await self._get_or_exc(
            target_user_id,
            load_bookings=load_bookings,
        )

    async def update(self, current_user: User, target_user_id: int, **fields) -> User:
        """
        Обновление пользователя:
        Сотрудник - может менять поля username и только для самого себя.
        Администратор - может менять любое поле (кроме id) любого профиля.
        """
        self._check_permission(current_user, target_user_id)
        if "role" in fields and current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Только администратор может изменять роль.")

        user = await self._get_or_exc(target_user_id)

        if "password" in fields:
            fields["password_hash"] = hash_password(fields.pop("password"))

        try:
            updated_user = await self.repo.update(user, **fields)
            await self.session.commit()
            return updated_user
        except IntegrityError as e:
            await self._handle_integrity_error(e)

    async def delete(self, current_user: User, user_id: int) -> None:
        """
        Только администратор может удалять пользователей.
        """
        # Если пользователи сами могут себя удалять -
        # то заменить этот if на if в комментарии:
        # if current_user.role != user.ADMIN and current_user_id != target_user_id:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError(
                "Только администратор может удалять других пользователей."
            )
        user = await self._get_or_exc(user_id)
        await self.repo.delete(user)
        await self.session.commit()
