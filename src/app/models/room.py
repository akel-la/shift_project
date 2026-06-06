import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Time
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.base import Base


class Room(Base):
    """
    Таблица комнат.
    """

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column()
    room_slots: Mapped[list["RoomSlot"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class RoomSlot(Base):
    """
    Набор временных слотов, которые разрешены для каждой комнаты.
    У разных комнат могут быть разные наборы интервалов.

    Запись в таблицу - только для администраторов.

    Не может быть несколько интервалов с одинаковым началом
    или одинаковым концом в одной и той же комнате.

    Проверки на уровне БД не защищают подобных записей:
    'комната 1, начало в 9:00, конец в 11:00'
    'комната 1, начало в 8:00, конец в 12:00'
    """

    __tablename__ = "room_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)

    room: Mapped[Room] = relationship(back_populates="room_slots")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="room_slot")

    __table_args__ = (
        UniqueConstraint("room_id", "start_time", name="uq_room_id_start_time"),
        UniqueConstraint("room_id", "end_time", name="uq_room_id_end_time"),
        CheckConstraint("start_time < end_time", name="ch_start_before_end"),
    )


class Booking(Base):
    """
    Записи о бронировании пользователей.
    """

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Добавить позже, при создании файла User и таблицы User в ней:
    # user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = False)
    # user[list[Booking]] relationship(back_populates = "bookings")
    room_slot_id: Mapped[int] = mapped_column(
        ForeignKey("room_slots.id"), nullable=False
    )
    booking_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    room_slot: Mapped["RoomSlot"] = relationship(back_populates="bookings")

    __table_args__ = (
        UniqueConstraint(
            "room_slot_id", "booking_date", name="uq_room_slot_id_booking_date"
        ),
    )
