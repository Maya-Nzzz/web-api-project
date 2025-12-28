from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False) # Объект, который управляет соединениями с БД.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False) # Фабрика для создания новых асинхронных сессий.


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
