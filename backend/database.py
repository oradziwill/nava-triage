from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from models.ticket import Ticket  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE tickets "
            "ADD COLUMN IF NOT EXISTS tasks JSONB, "
            "ADD COLUMN IF NOT EXISTS ai_title VARCHAR(255)"
        ))
