from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room


class RoomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, room: Room) -> Room:
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def get_all(self) -> list[Room]:
        result = await self.session.execute(select(Room))
        return result.scalars().all()
