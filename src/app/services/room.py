from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.exceptions import NotFoundError
from app.models.room import Room
from app.repositories.room import RoomRepository


# Create, Update и Delete комнаты - только для администраторов,
# поэтому здесь нет проверок прав, вместо этого ендпоинты только для админов.
class RoomService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RoomRepository(session)

    async def _get_or_exc(self, room_id: int, *, load_slots: bool = False) -> Room:
        room = await self.repo.get_by_id(room_id, load_slots=load_slots)
        if not room:
            raise NotFoundError(f"Комната с id = {room_id} не найдена.")
        return room

    async def _handle_integrity_error(self, error: IntegrityError, name: str) -> None:
        await self.session.rollback()
        raise ConflictError(f"Комната с именем {name} уже существует.") from error

    async def create(self, name: str, description: str | None = None) -> Room:
        try:
            room = await self.repo.create(
                name=name,
                description=description,
            )
            await self.session.commit()
            return room
        except IntegrityError as e:
            await self._handle_integrity_error(e, name)

    async def get_by_id(self, room_id: int, *, load_slots: bool = False) -> Room:
        return await self._get_or_exc(room_id, load_slots=load_slots)

    async def get_all(self, *, load_slots: bool = False) -> Sequence[Room]:
        return await self.repo.get_all(load_slots=load_slots)

    async def update(self, room_id: int, **fields) -> Room:
        room = await self._get_or_exc(room_id)
        try:
            updated_room = await self.repo.update(room, **fields)
            await self.session.commit()
            return updated_room
        except IntegrityError as e:
            await self._handle_integrity_error(e, fields.get("name", "unknown"))

    async def delete(self, room_id: int) -> None:
        room = await self._get_or_exc(room_id)
        await self.repo.delete(room)
        await self.session.commit()
