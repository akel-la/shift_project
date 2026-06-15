from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.booking import router as booking_router
from app.api.v1.room import router as rooms_router
from app.api.v1.slot import room_slots_router
from app.api.v1.slot import router as slots_router
from app.api.v1.user import router as users_router
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.exception_handlers import service_exception_handler
from app.core.exceptions import *  # noqa
from app.services.auth import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Автоматически создаем первого администратора,
    если он уже не в БД.
    """
    if settings.CREATE_INITIAL_ADMIN:
        async with async_session_maker() as session:
            auth_service = AuthService(session)
            await auth_service.create_admin_if_not_exists()
    yield


app = FastAPI(lifespan=lifespan)


app.add_exception_handler(ServiceError, service_exception_handler)


app.include_router(rooms_router, prefix="/api/v1")
app.include_router(slots_router, prefix="/app/v1")
app.include_router(room_slots_router, prefix="/app/v1")
# Изменили URL - меняем и URL в OAuth2PasswordBearer в этом проекте:
app.include_router(auth_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")
# Добавить, если понадобится:
# if settings.ENABLE_ADMIN_REGISTRATION_ENDPOINT:
app.include_router(admin_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
