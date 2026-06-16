import datetime

from pydantic import model_validator
from pydantic import field_validator
from pydantic import Field

from app.core.schema import BaseSchema


class SlotBase(BaseSchema):
    start_time: datetime.time
    end_time: datetime.time

    @model_validator(mode="after")
    def time_time_order(self):
        if self.start_time >= self.end_time:
            raise ValueError("'start_time' должно быть раньше, чем 'end_time'")
        return self

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_time(cls, v: datetime.time) -> datetime.time:
        """
        Приводим время к одному формату.
        """
        return v.replace(second=0, microsecond=0, tzinfo=None)


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
    id: int = Field(gt=0)
    room_id: int = Field(gt=0)


class SlotResponse(SlotCreateResponse):
    pass
