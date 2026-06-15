import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import Time
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.base import Base

if TYPE_CHECKING:
    from .booking import Booking
    from .room import Room


# Везде используем просто slot (коротко), а не roomslot, но в названии
# таблицы  на уровне БД назовем room_slots, чтобы связь была более понятной:
class Slot(Base):
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

    room: Mapped["Room"] = relationship(back_populates="slots")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="slot",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("room_id", "start_time", name="uq_room_id_start_time"),
        UniqueConstraint("room_id", "end_time", name="uq_room_id_end_time"),
        CheckConstraint("start_time < end_time", name="ch_start_before_end"),
    )
