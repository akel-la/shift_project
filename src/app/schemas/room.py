import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        # Запрос с лишним полем - ошибка 422, чтобы пользователь
        # знал, что его запрос не корректный:
        extra="forbid",
        from_attributes=True,
    )


# --- Room ---:


class RoomBase(BaseSchema):
    name: str
    description: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: int


# --Slot ---:


class SlotBase(BaseSchema):
    start_time: datetime.time
    end_time: datetime.time

    @model_validator(mode="after")
    def time_interval(self):
        if self.start_time >= self.end_time:
            raise ValueError("'start_time' должно быть раньше, чем 'end_time'")
        return self


class SlotCreate(SlotBase):
    # room_id: int не нужен,
    pass


class SlotResponse(SlotBase):
    id: int
    room_id: int
