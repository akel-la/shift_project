import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.exceptions import NotFoundError
from app.models.room import Room
from app.models.room import RoomSlot
from app.repositories.room import RoomRepository
from app.repositories.room import RoomSlotRepository


class RoomService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RoomRepository(session)

    async def get_room(self, room_id: int, *, load_slots: bool = False) -> Room | None:
        return await self.repo.get_room(room_id, load_slots=load_slots)

    async def create_room(self, name: str, description: str | None = None) -> Room:
        try:
            room = await self.repo.create_room(
                name=name,
                description=description,
            )
            await self.session.commit()
            return room
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"Комната с именем '{name}' уже существует.") from e

    async def get_all_rooms(self, *, load_slots: bool = False) -> list[Room]:
        return await self.repo.get_all_rooms(load_slots=load_slots)


class RoomSlotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RoomSlotRepository(session)
        self.room_repo = RoomRepository(session)

    # Подумать, как сюда добавить load_room - возможно, переработать
    # метод в репозитории:
    async def get_roomslot(self, roomslot_id: int) -> RoomSlot | None:
        return await self.repo.get_roomslot(roomslot_id)

    async def create_roomslot(
        self, room_id: int, start_time: datetime.time, end_time: datetime.time
    ) -> RoomSlot:
        # Заменить на обработку ошибки?
        room = await self.room_repo.get_room(room_id)
        if not room:
            raise NotFoundError(f"Комната с id = {room_id} не найдена.")
        try:
            roomslot = await self.repo.create_roomslot(
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
            )
            await self.session.commit()
            return roomslot
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(
                "Слот с таким временем начала или окончания "
                "уже существует в этой комнате."
            ) from e

    async def get_all_roomslots(self, *, load_room: bool = False) -> list[RoomSlot]:
        return await self.repo.get_all_roomslots(load_room=load_room)

    async def get_all_roomslots_from_room_id(
        self, room_id: int, *, load_room: bool = False
    ) -> list[RoomSlot]:
        return await self.repo.get_all_roomslots_from_room_id(
            room_id, load_room=load_room
        )
