from datetime import date
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.user import UserRole
from app.schemas.booking import BookingCreate
from app.schemas.booking import BookingResponse
from app.services.booking import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: BookingCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Создать бронирование от своего имени (роль не важна)."""
    service = BookingService(session)
    return await service.create(
        slot_id=data.slot_id,
        current_user=current_user,
        booking_date=data.booking_date,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get(
    booking_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Получить конкретное бронирование с проверкой доступа."""
    service = BookingService(session)
    return await service.get_booking(current_user, booking_id)


@router.get("", response_model=list[BookingResponse])
async def get_all(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    room_id: Annotated[int | None, Query()] = None,
    date_filter: Annotated[date | None, Query(alias="date")] = None,
    user_id: Annotated[int | None, Query()] = None,
):
    """
    Получить список бронирований с возможностью фильтрации.
    - Администратор может указать `user_id` для просмотра чужих броней.
    - Сотрудник видит только свои бронирования (параметр `user_id` игнорируется).
    - Можно фильтровать по `room_id` и `date`.
    """
    service = BookingService(session)

    # Сотрудник всегда видит только свои бронирования:
    if current_user.role != UserRole.ADMIN:
        user_id = current_user.id

    return await service.get_by_filter(
        room_ids=[room_id] if room_id is not None else None,
        booking_dates=[date_filter] if date_filter is not None else None,
        user_id=user_id,
    )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    booking_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Отменить бронирование (сотрудник — своё, администратор — любое)."""
    service = BookingService(session)
    await service.delete(current_user, booking_id)
