import enum
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.base import Base

if TYPE_CHECKING:
    from .booking import Booking


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        default=UserRole.EMPLOYEE,
        # server_default=UserRole.EMPLOYEE.value
        # может не сработать для некоторых диалектов:
        server_default=text("'employee'"),
        nullable=False,
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
