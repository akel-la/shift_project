from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dependencies.auth import get_current_admin_user
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.room import RoomCreate
from app.schemas.room import RoomCreateResponse
from app.schemas.room import RoomResponse
from app.schemas.room import RoomUpdate
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomCreateResponse, status_code=status.HTTP_201_CREATED)
async def create(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    data: RoomCreate,
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = RoomService(session)
    return await service.create(
        name=data.name,
        description=data.description,
    )


@router.get("/{room_id}", response_model=RoomResponse)
async def get(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    room_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    load_slots: bool = False,
):
    service = RoomService(session)
    return await service.get_by_id(room_id, load_slots=load_slots)


@router.get("", response_model=list[RoomResponse])
async def get_all(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    load_slots: bool = False,
):
    service = RoomService(session)
    return await service.get_all(load_slots=load_slots)


@router.put("/{room_id}", response_model=RoomCreateResponse)
async def update(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    room_id: int,
    data: RoomUpdate,
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = RoomService(session)
    return await service.update(room_id, **data.model_dump(exclude_unset=True))


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    room_id: int,
    _admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = RoomService(session)
    await service.delete(room_id)
