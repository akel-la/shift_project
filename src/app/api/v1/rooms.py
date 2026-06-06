from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import ConflictError
from app.core.exceptions import NotFoundError
from app.schemas.room import RoomCreate
from app.schemas.room import RoomResponse
from app.schemas.room import SlotCreate
from app.schemas.room import SlotResponse
from app.services.room import RoomService
from app.services.room import RoomSlotService

router = APIRouter(prefix="/booking", tags=["booking"])

# --- Rooms ---:


@router.get("/room/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomService(session)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена."
        )
    return RoomResponse.model_validate(room)


@router.get("/rooms", response_model=list[RoomResponse])
async def get_all_rooms(
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomService(session)
    rooms = await service.get_all_rooms()
    return [RoomResponse.model_validate(r) for r in rooms]


@router.post("/room", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomService(session)
    try:
        room = await service.create_room(
            name=data.name,
            description=data.description,
        )
        return RoomResponse.model_validate(room)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e


# --- RoomSlots ---:


# Не понятно, нужна ли вообще такая ручка?
@router.get("/slot/{roomslot_id}", response_model=SlotResponse)
async def get_roomslot(
    roomslot_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomSlotService(session)
    roomslot = await service.get_roomslot(roomslot_id)
    if not roomslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Слот не найден."
        )
    return SlotResponse.model_validate(roomslot)


@router.get("/rooms/slots", response_model=list[SlotResponse])
async def get_all_roomslots(
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomSlotService(session)
    slots = await service.get_all_roomslots()
    return [SlotResponse.model_validate(s) for s in slots]


@router.get("/room/{room_id}/slots", response_model=list[SlotResponse])
async def get_all_roomslots_from_room_id(
    room_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    room_service = RoomService(session)
    room = await room_service.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена."
        )
    service = RoomSlotService(session)
    slots = await service.get_all_roomslots_from_room_id(room_id)
    return [SlotResponse.model_validate(s) for s in slots]


@router.post(
    "/{room_id}/slot", response_model=SlotResponse, status_code=status.HTTP_201_CREATED
)
async def create_roomslot(
    room_id: int,
    data: SlotCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = RoomSlotService(session)
    try:
        slot = await service.create_roomslot(
            room_id=room_id,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        return SlotResponse.model_validate(slot)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
