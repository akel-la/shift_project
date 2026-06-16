from datetime import date

from pydantic import field_validator
from pydantic import Field

from app.core.schema import BaseSchema


class BookingBase(BaseSchema):
    slot_id: int = Field(gt=0)
    booking_date: date

    @field_validator("booking_date")
    @classmethod
    def date_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Дата бронирования не может быть в прошлом.")
        return v


class BookingCreate(BookingBase):
    # user_id берется из JWT токена.
    pass


class BookingCreateResponse(BookingBase):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)


class BookingResponse(BookingCreateResponse):
    pass
