from pydantic import BaseModel

from app.models.room import TimeSlot


class RoomBase(BaseModel):
    time_slot: TimeSlot


class RoomCreate(RoomBase):
    pass


class RoomRead(RoomBase):
    id: int

    model_config = {"from_attributes": True}
