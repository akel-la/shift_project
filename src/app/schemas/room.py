from app.core.schema import BaseSchema
from app.schemas.slot import SlotResponse


class RoomBase(BaseSchema):
    name: str
    description: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomCreateResponse(RoomBase):
    id: int


# Наследуемся от BaseSchema, чтобы не было обязательного поля name:
class RoomUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None


class RoomResponse(RoomCreateResponse):
    slots: list[SlotResponse] = []
