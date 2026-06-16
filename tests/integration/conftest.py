"""
Здесь все, что нужно только для интеграционных тестов.
"""
import os  # noqa

# Меняем переменную до импорта app из main:
os.environ["CREATE_INITIAL_ADMIN"] = "false"  # noqa

import datetime
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

# Импорт пакета - регистрация таблиц в Base.metadata:
from app.core.base import Base
from app.core.database import get_async_session
from app.core.security import hash_password

# app - пакет, application - объект FastAPI:
from app.main import app as application
from app.models.room import Room
from app.models.slot import Slot
from app.models.user import User


@pytest.fixture(scope="session")
def tmp_db_path(tmp_path_factory):
    """
    Создаем путь для временного файла тестовой БД.
    Одно создание файла на всю сессию тестов.
    """
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest_asyncio.fixture(scope="session")
async def test_engine(tmp_db_path):
    """
    Создаем асинхронный движок, привязанный к временному файлу.
    Создает все таблицы перед тестами и удаляет их после.
    """
    test_db_url = f"sqlite+aiosqlite:///{tmp_db_path.as_posix()}"
    engine = create_async_engine(test_db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """ """
    async_session_factory = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        # Внешняя транзакция - транзакция теста, результаты тестов всегда rollback,
        # никогда не commit, чтобы по окончании теста содержимое БД оставалось прежним:
        # ВАЖНО! Не используем with ... as ...,
        # так как тут он делает автоматический commit:
        outer_transaction = await session.begin()
        try:
            # Вложенная транзакция (savepoint) - для тестируемого кода:
            # Тестируемый код может commit или rollback вложенной транзакции,
            # в зависимости от того, позитивное или негативное тестирование:
            await session.begin_nested()
            yield session
        finally:
            # Пытаемся rollback внешнюю транзакцию. Если она уже была rollback -
            # то просто перехватываем исключение "Транзакция уже закрыта":
            try:
                await outer_transaction.rollback()
            except ResourceClosedError:
                pass


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_db(test_engine):
    """
    Очищает все таблицы после каждого теста.
    """
    # Отдельная сессия, очищающая таблицы:
    async_session_factory = async_sessionmaker(test_engine)
    async with async_session_factory() as session:
        # Удалить все записи из всех таблиц:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()


@pytest_asyncio.fixture(scope="function", autouse=True)
def override_get_session(db_session):
    """
    Подмена get_async_session в Depends fastapi ручек.
    Автоматически вызывается, после теста - удаляет переопределение.
    """

    async def _override():
        yield db_session

    application.dependency_overrides[get_async_session] = _override
    yield
    application.dependency_overrides.pop(get_async_session, None)


# Обычные таблицы:

# Slot:

@pytest_asyncio.fixture(scope="function")
async def test_slot(db_session: AsyncSession, test_room):
    slot = Slot(
        room_id=test_room.id,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
    )
    db_session.add(slot)
    await db_session.flush()
    return slot


# Room:


@pytest_asyncio.fixture(scope="function")
async def test_room(db_session: AsyncSession):
    room = Room(name="Переговорка 1", description="Тестовая комната")
    db_session.add(room)
    await db_session.flush()
    return room


# Пользователи (сотрудники и администраторы) и токены:


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Асинхронный HTTP-клиент для тестирования.
    Реальных сетевых вызовов не происходит.
    """
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    """
    Создает администратора в тестовой БД, возвращает объект User.
    Пароль хешируется при создании, используется для последующей
    аутентификации.
    """
    user = User(
        username="admin",
        password_hash=hash_password("12345somepassword12345"),
        role="admin",
    )
    db_session.add(user)
    # flush - чтобы получить id.
    # Не используем commit, так как db_session сделает rollback.
    await db_session.flush()
    return user


@pytest_asyncio.fixture(scope="function")
async def employee_user(db_session: AsyncSession):
    """
    Создание обычного сотрудника.
    """
    user = User(
        username="employee",
        password_hash=hash_password("emp123456"),
        role="employee",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture(scope="function")
async def employee_token(client: AsyncClient, employee_user):
    """
    Получение access token сотрудника.
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "employee",
            "password": "emp123456",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def admin_token(client: AsyncClient, admin_user):
    """
    Получение access token администратора.
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "12345somepassword12345",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]
