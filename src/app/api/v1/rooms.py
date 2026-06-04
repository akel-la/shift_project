from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.repositories.room import RoomRepository
from app.schemas.room import RoomCreate
from app.schemas.room import RoomRead
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


def get_room_service(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> RoomService:
    repo = RoomRepository(db)
    return RoomService(repo)


@router.post("/", response_model=RoomRead, status_code=201)
async def create_room(
    room_data: RoomCreate,
    service: Annotated[RoomService, Depends(get_room_service)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    return await service.create_room(room_data)


@router.get("/", response_model=list[RoomRead])
async def list_rooms(
    service: Annotated[RoomService, Depends(get_room_service)],
):
    return await service.get_rooms()
