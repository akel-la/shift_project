from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room


class RoomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Room:
        room = Room(name=name, description=description)
        self.session.add(room)
        await self.session.flush()
        return room

    async def get_by_id(self, room_id: int, *, load_slots: bool = False) -> Room | None:
        stmt = select(Room).where(Room.id == room_id)
        if load_slots:
            stmt = stmt.options(selectinload(Room.slots))
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def get_all(self, *, load_slots: bool = False) -> Sequence[Room]:
        """
        Позволяет за один запрос к БД получить:
        1. Все комнаты.
        2. Все комнаты и их слоты.
        """
        stmt = select(Room)
        if load_slots:
            stmt = stmt.options(selectinload(Room.slots))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, room: Room, **fields) -> Room:
        for field, value in fields.items():
            if hasattr(room, field):
                setattr(room, field, value)
        await self.session.flush()
        return room

    async def delete(self, room: Room) -> None:
        await self.session.delete(room)
        await self.session.flush()
