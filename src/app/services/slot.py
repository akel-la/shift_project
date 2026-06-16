import datetime
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.exceptions import NotFoundError
from app.models.slot import Slot
from app.repositories.room import RoomRepository
from app.repositories.slot import SlotRepository


class SlotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SlotRepository(session)
        self.room_repo = RoomRepository(session)


    async def _get_or_exc(self, slot_id: int) -> Slot:
        slot = await self.repo.get_by_id(slot_id)
        if not slot:
            raise NotFoundError(f"Слот с id = {slot_id} не найден.")
        return slot


    async def _handle_integrity_error(
        self, error: IntegrityError, room_id: int
    ) -> None:
        await self.session.rollback()
        # Даты не правильные, объекта нет и тому подобное - разные причины:
        raise ConflictError(
            f"Нарушение целостности данных при работе со слотом"
            f" в комнате id = {room_id}."
        ) from error


    async def create(
        self, room_id: int, start_time: datetime.time, end_time: datetime.time
    ) -> Slot:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Комната с id = {room_id} не найдена.")
        try:
            slot = await self.repo.create(
                room_id=room_id,
                start_time=start_time,
                end_time=end_time,
            )
            await self.session.commit()
            return slot
        except IntegrityError as e:
            await self._handle_integrity_error(e, room_id)


    async def get_by_id(self, slot_id: int) -> Slot:
        return await self._get_or_exc(slot_id)


    async def get_all(self, *, load_room: bool = False) -> Sequence[Slot]:
        return await self.repo.get_all(load_room=load_room)


    async def get_all_by_room_id(
        self,
        room_id: int,
        *,
        load_room: bool = False,
    ) -> Sequence[Slot]:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Комната с id = {room_id} не найдена.")
        return await self.repo.get_all_by_room_id(
            room_id=room_id,
            load_room=load_room,
        )


    async def update(self, slot_id: int, **fields) -> Slot:
        slot = await self._get_or_exc(slot_id)
        try:
            updated_slot = await self.repo.update(slot, **fields)
            await self.session.commit()
            return updated_slot
        except IntegrityError as e:
            await self._handle_integrity_error(e, slot.room_id)


    async def delete(self, slot_id: int) -> None:
        slot = await self._get_or_exc(slot_id)
        await self.repo.delete(slot)
        await self.session.commit()
