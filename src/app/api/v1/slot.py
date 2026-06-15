from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dependencies.auth import get_current_admin_user
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.slot import SlotCreate
from app.schemas.slot import SlotResponse
from app.schemas.slot import SlotUpdate
from app.services.slot import SlotService

# Глобальные операции со слотами (независимо от комнаты)
router = APIRouter(prefix="/slots", tags=["slots"])

# Операции со слотами в контексте конкретной комнаты
room_slots_router = APIRouter(
    prefix="/rooms/{room_id}/slots",
    tags=["room_slots"],
)


# --- /slots ---


@router.get("/{slot_id}", response_model=SlotResponse)
async def get(
    slot_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    load_room: bool = False,
):
    service = SlotService(session)
    return await service.get_by_id(slot_id)


@router.get("", response_model=list[SlotResponse])
async def get_all(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    load_room: bool = False,
):
    service = SlotService(session)
    return await service.get_all(load_room=load_room)


@router.put("/{slot_id}", response_model=SlotResponse)
async def update(
    slot_id: int,
    data: SlotUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = SlotService(session)
    return await service.update(
        slot_id=slot_id,
        **data.model_dump(exclude_unset=True),
    )


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    slot_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = SlotService(session)
    await service.delete(slot_id)


# --- /rooms/{room_id}/slots ---


@room_slots_router.post(
    "", response_model=SlotResponse, status_code=status.HTTP_201_CREATED
)
async def create_for_room(
    room_id: int,
    data: SlotCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = SlotService(session)
    return await service.create(
        room_id=room_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )


@room_slots_router.get("", response_model=list[SlotResponse])
async def get_all_for_room(
    room_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    load_room: bool = False,
):
    service = SlotService(session)
    return await service.get_all_by_room_id(
        room_id=room_id,
        load_room=load_room,
    )
