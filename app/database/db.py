from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine,async_sessionmaker
from app.settings import Config

DATABASE_URL = Config.DB_URL

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL,echo=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
    )

    async with async_session() as session:
        yield session
