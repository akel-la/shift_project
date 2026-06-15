import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.base import Base

if TYPE_CHECKING:
    from .slot import Slot
    from .user import User


class Booking(Base):
    """
    Записи о бронировании пользователей.
    """

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="bookings")

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("room_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_date: Mapped[datetime.date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    slot: Mapped["Slot"] = relationship(back_populates="bookings")

    __table_args__ = (
        UniqueConstraint("slot_id", "booking_date", name="uq_slot_id_booking_date"),
    )
