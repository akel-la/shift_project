from app.core.schema import BaseSchema
from app.schemas.slot import SlotResponse
from pydantic import Field


class RoomBase(BaseSchema):
    name: str
    description: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomCreateResponse(RoomBase):
    id: int = Field(gt=0)


# Наследуемся от BaseSchema, чтобы не было обязательного поля name:
class RoomUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None


class RoomResponse(RoomCreateResponse):
    slots: list[SlotResponse] = []
