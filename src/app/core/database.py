from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from .config import settings

# Асинхронный движок - для асинхронного проекта (FastAPI, SQLAlchemy):
engine = create_async_engine(
    settings.DATABASE_URL,
    # По умолчанию False, но можно поменять
    # на True, если ищем баг на уровне ORM-БД:
    echo=False,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    # После коммита объекты по прежнему можно использовать,
    # без необходимости нагружать БД запросами на извлечение этих объектов.
    # Необходим для асинхронных запросов, так как асинхронные запросы не
    # поддерживают неявные запросы в БД для обновления не свежих данных:
    expire_on_commit=False,
)


async def get_async_session():
    """Использование:
    session: AsyncSession = Depends(get_async_session)
    FastAPI вызывает фабрику, фабрика производит сессию, FastAPI ручка
    получает сессию, сессия автоматически закроется
    (нет автоматического commit)
    ВАЖНО! Никогда в самих ручках не вызывать:
    async with get_async_session."""
    async with async_session_maker() as session:
        yield session
