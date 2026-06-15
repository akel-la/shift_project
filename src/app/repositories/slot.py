import datetime
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.slot import Slot


class SlotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        room_id: int,
        start_time: datetime.time,
        end_time: datetime.time,
    ) -> Slot:
        slot = Slot(
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(slot)
        await self.session.flush()
        return slot

    async def get_by_id(self, slot_id: int) -> Slot | None:
        return await self.session.get(Slot, slot_id)

    async def get_all(self, *, load_room: bool = False) -> Sequence[Slot]:
        stmt = select(Slot)
        if load_room:
            stmt = stmt.options(selectinload(Slot.room))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_by_room_id(
        self,
        room_id: int,
        *,
        load_room: bool = False,
    ) -> Sequence[Slot]:
        stmt = select(Slot).where(Slot.room_id == room_id)
        if load_room:
            stmt = stmt.options(selectinload(Slot.room))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, slot: Slot, **fields) -> Slot:
        for field, value in fields.items():
            if hasattr(slot, field):
                setattr(slot, field, value)
        await self.session.flush()
        return slot

    async def delete(self, slot: Slot) -> None:
        await self.session.delete(slot)
        await self.session.flush()
