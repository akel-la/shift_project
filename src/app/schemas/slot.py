import datetime

from pydantic import model_validator

from app.core.schema import BaseSchema


class SlotBase(BaseSchema):
    start_time: datetime.time
    end_time: datetime.time

    @model_validator(mode="after")
    def time_time_order(self):
        if self.start_time >= self.end_time:
            raise ValueError("'start_time' должно быть раньше, чем 'end_time'")
        return self


class SlotCreate(SlotBase):
    # room_id: int не нужен, room_id содержится в URL запросе.
    pass


class SlotUpdate(BaseSchema):
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None

    @model_validator(mode="after")
    def check_time_order(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("'start_time' должно быть раньше, чем 'end_time")
        return self


class SlotCreateResponse(SlotBase):
    id: int
    room_id: int


class SlotResponse(SlotCreateResponse):
    pass
