import datetime
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.exceptions import ForbiddenError
from app.core.exceptions import NotFoundError
from app.models.booking import Booking
from app.models.user import User
from app.models.user import UserRole
from app.repositories.booking import BookingRepository
from app.repositories.slot import SlotRepository


class BookingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BookingRepository(session)
        self.slot_repo = SlotRepository(session)

    async def _get_or_exc(self, booking_id: int) -> Booking:
        booking = await self.repo.get_by_id(booking_id)
        if not booking:
            raise NotFoundError(f"Бронирование с id = {booking_id} не найдено.")
        return booking

    async def _handle_integrity_error(self, error: IntegrityError) -> None:
        await self.session.rollback()
        raise ConflictError(
            "Нарушение целостности данных при работе с бронированием."
        ) from error

    def _check_permission(self, current_user: User, user_id: int, msg: str):
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            raise ForbiddenError(f"{msg}")

    async def create(
        self,
        slot_id: int,
        current_user: User,
        booking_date: datetime.date,
    ) -> Booking:
        slot = await self.slot_repo.get_by_id(slot_id)
        if not slot:
            raise NotFoundError(f"Слот с id={slot_id} не найден.")
        existing = await self.repo.get_by_slot_and_date(slot_id, booking_date)
        if existing:
            raise ConflictError("Этот слот уже забронирован на выбранную дату.")
        try:
            booking = await self.repo.create(
                user_id=current_user.id,
                slot_id=slot_id,
                booking_date=booking_date,
            )
            await self.session.commit()
            return booking
        except IntegrityError as e:
            await self._handle_integrity_error(e)

    async def get_by_id(self, booking_id: int) -> Booking:
        return await self._get_or_exc(booking_id)

    async def get_booking(self, current_user: User, booking_id: int) -> Booking:
        """
        Получить бронь с проверкой: сотрудник только свою, админ любую.
        """
        booking = await self._get_or_exc(booking_id)
        self._check_permission(
            current_user,
            booking.user_id,
            msg="Вы можете просматривать только свои бронирования.",
        )
        return booking

    async def get_by_slot_and_date(
        self,
        slot_id: int,
        booking_date: datetime.date,
    ) -> Booking | None:
        return await self.repo.get_by_slot_and_date(
            slot_id=slot_id,
            booking_date=booking_date,
        )

    async def get_all_by_date(
        self,
        booking_date: datetime.date,
    ) -> Sequence[Booking]:
        return await self.repo.get_all_by_date(
            booking_date=booking_date,
        )

    async def get_all_by_room_id(
        self,
        room_id: int,
    ) -> Sequence[Booking]:
        return await self.repo.get_all_by_room_id(room_id=room_id)

    async def get_by_filter(
        self,
        *,
        room_ids: Sequence[int] | None = None,
        slot_ids: Sequence[int] | None = None,
        booking_dates: Sequence[datetime.date] | None = None,
        user_id: int | None = None,
    ) -> Sequence[Booking]:
        return await self.repo.get_by_filter(
            room_ids=room_ids,
            slot_ids=slot_ids,
            booking_dates=booking_dates,
            user_id=user_id,
        )

    async def delete(
        self,
        current_user: User,
        booking_id: int,
    ) -> None:
        booking = await self._get_or_exc(booking_id)
        self._check_permission(
            current_user=current_user,
            user_id=booking.user_id,
            msg="Вы можете отменять только свои бронирования.",
        )
        await self.repo.delete(booking)
        await self.session.commit()
