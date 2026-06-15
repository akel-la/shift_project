from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user import UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        username: str,
        password_hash: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(
        self,
        user_id: int,
        load_bookings: bool = False,
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if load_bookings:
            stmt = stmt.options(selectinload(User.bookings))
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def get_by_username(
        self,
        username: str,
        load_bookings: bool = False,
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        if load_bookings:
            stmt = stmt.options(selectinload(User.bookings))
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def update(self, user: User, **fields) -> User:
        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
