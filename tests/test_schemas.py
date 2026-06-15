import datetime

import pytest
from pydantic import ValidationError

from app.schemas.booking import BookingCreate
from app.schemas.room import RoomCreate
from app.schemas.room import RoomUpdate
from app.schemas.slot import SlotCreate
from app.schemas.slot import SlotUpdate


class TestRoomSchema:
    def test_room_create_requires_name(self):
        with pytest.raises(ValidationError):
            RoomCreate()  # name обязателен

    def test_room_create_valid(self):
        room = RoomCreate(name="Переговорка")
        assert room.name == "Переговорка"

    def test_room_update_exclude_unset(self):
        # Только изменяемые поля
        update = RoomUpdate(description="Новое описание")
        data = update.model_dump(exclude_unset=True)
        assert "name" not in data
        assert data["description"] == "Новое описание"


class TestSlotSchema:
    def test_slot_create_invalid_time_order(self):
        with pytest.raises(ValidationError):
            SlotCreate(start_time=datetime.time(12, 0), end_time=datetime.time(10, 0))

    def test_slot_create_valid(self):
        slot = SlotCreate(
            start_time=datetime.time(10, 0), end_time=datetime.time(12, 0)
        )
        assert slot.start_time == datetime.time(10, 0)

    def test_slot_update_partial_time_fails_if_order_invalid(self):
        with pytest.raises(ValidationError):
            SlotUpdate(start_time=datetime.time(15, 0), end_time=datetime.time(13, 0))

    def test_slot_update_single_field_ok(self):
        update = SlotUpdate(start_time=datetime.time(9, 0))
        data = update.model_dump(exclude_unset=True)
        assert "end_time" not in data
        assert data["start_time"] == datetime.time(9, 0)


class TestBookingSchema:
    def test_booking_create_past_date(self):
        with pytest.raises(ValidationError):
            BookingCreate(slot_id=1, booking_date=datetime.date(2020, 1, 1))

    def test_booking_create_future_date_ok(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        booking = BookingCreate(slot_id=1, booking_date=tomorrow)
        assert booking.booking_date == tomorrow
