from app.models.room import Room
from app.repositories.room import RoomRepository
from app.schemas.room import RoomCreate
from app.schemas.room import RoomRead


class RoomService:
    def __init__(self, repository: RoomRepository):
        self.repo = repository

    async def create_room(self, room_data: RoomCreate) -> RoomRead:
        room = Room(time_slot=room_data.time_slot)
        created = await self.repo.create(room)
        return RoomRead.model_validate(created)

    async def get_rooms(self) -> list[RoomRead]:
        rooms = await self.repo.get_all()
        return [RoomRead.model_validate(r) for r in rooms]
