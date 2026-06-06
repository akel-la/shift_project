import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room
from app.models.room import RoomSlot


class RoomRepository:
    """
    Репозитории:

    Не делают коммитов.
    Не работают с Pydantic схемами.
    Возвращают экземпляры Классов-таблиц.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_room(self, room_id: int, *, load_slots: bool = False) -> Room | None:
        stmt = select(Room).where(Room.id == room_id)
        if load_slots:
            stmt = stmt.options(selectinload(Room.room_slots))
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def create_room(self, name: str, description: str | None = None) -> Room:
        room = Room(name=name, description=description)
        self.session.add(room)
        await self.session.flush()
        return room

    async def get_all_rooms(self, *, load_slots: bool = False) -> list[Room]:
        stmt = select(Room)
        if load_slots:
            stmt = stmt.options(selectinload(Room.room_slots))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class RoomSlotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_roomslot(self, slot_id: int) -> RoomSlot | None:
        return await self.session.get(RoomSlot, slot_id)

    async def create_roomslot(
        self,
        room_id: int,
        start_time: datetime.time,
        end_time: datetime.time,
    ) -> RoomSlot:
        roomslot = RoomSlot(
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(roomslot)
        await self.session.flush()
        return roomslot

    async def get_all_roomslots_from_room_id(
        self, room_id: int, *, load_room=False
    ) -> list[RoomSlot]:
        stmt = select(RoomSlot).where(RoomSlot.room_id == room_id)
        if load_room:
            stmt = stmt.options(selectinload(RoomSlot.room))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_roomslots(self, *, load_room: bool = False) -> list[RoomSlot]:
        stmt = select(RoomSlot)
        if load_room:
            stmt = stmt.options(selectinload(RoomSlot.room))
        result = await self.session.execute(stmt)
        return result.scalars().all()
