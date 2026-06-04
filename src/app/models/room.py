from enum import Enum as PyEnum  # PyEnum - это Enum самого Python.

from sqlalchemy import Enum as SAEnum  # SAEnum - это Enum на уровне SQLAlchemy.
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.base import Base


class TimeSlot(str, PyEnum):  # noqa
    SLOT_09_11 = "09:00-11:00"
    SLOT_11_13 = "11:00-13:00"
    SLOT_13_15 = "13:00-15:00"


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    time_slot: Mapped[TimeSlot] = mapped_column(
        # SAEnum делает проверку на уровне БД,
        # что значение попадает под категорию.
        # name - это имя CHECK на уровне БД, задаем его, чтобы всегда
        # было одинаковым и не было проблем с Alembic:
        SAEnum(TimeSlot, name="time_slot_check"),
        nullable=False,
    )
