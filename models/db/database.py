from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config.manager import settings


Base = declarative_base()


def get_async_engine() -> AsyncEngine:
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(database_url, future=True, echo=settings.DEBUG)


async_engine: AsyncEngine = get_async_engine()
async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)

