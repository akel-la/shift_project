import datetime
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.slot import Slot


class BookingRepository:
    """
    Метода update нет, так как в ТЗ о нем не говорится.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        slot_id: int,
        booking_date: datetime.date,
    ) -> Booking:
        booking = Booking(
            user_id=user_id,
            slot_id=slot_id,
            booking_date=booking_date,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def get_by_id(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)

    async def get_by_slot_and_date(
        self,
        slot_id: int,
        booking_date: datetime.date,
    ) -> Booking | None:
        """Проверяем, не занята ли комната на это время."""
        stmt = select(Booking).where(
            Booking.slot_id == slot_id,
            Booking.booking_date == booking_date,
        )
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def get_all_by_date(
        self,
        booking_date: datetime.date,
    ) -> Sequence[Booking]:
        return await self.get_by_filter(
            booking_dates=[booking_date],
        )

    async def get_all_by_room_id(self, room_id: int) -> Sequence[Booking]:
        return await self.get_by_filter(room_ids=[room_id])

    async def get_by_filter(
        self,
        *,
        # Sequence - любая последовательность:
        room_ids: Sequence[int] | None = None,
        slot_ids: Sequence[int] | None = None,
        booking_dates: Sequence[datetime.date] | None = None,
        user_id: int | None = None,
    ) -> Sequence[Booking]:
        # Сделать комментарии, поясняющие то, как работает метод:
        """
        Поиск бронирования, с гибкой системой фильтров.
        """
        stmt = select(Booking)

        conditions = []
        if room_ids is not None:
            stmt = stmt.join(Booking.slot)
            conditions.append(Slot.room_id.in_(room_ids))
        if slot_ids is not None:
            conditions.append(Booking.slot_id.in_(slot_ids))
        if booking_dates is not None:
            conditions.append(Booking.booking_date.in_(booking_dates))

        if user_id is not None:
            conditions.append(Booking.user_id == user_id)

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, booking: Booking) -> None:
        await self.session.delete(booking)
        await self.session.flush()
