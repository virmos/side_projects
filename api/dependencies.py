from typing import AsyncGenerator, Type, Callable
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from models.db.database import async_session_factory
from models.db.types import IDatabase
from services.types import IPriceListLoader


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as async_session:
        try:
            yield async_session
        finally:
            await async_session.close()


def get_repository(repo_type: Type = None) -> Callable:
    def _get_repo(session: AsyncSession = fastapi.Depends(get_async_session)):
        return repo_type(async_session=session)

    return _get_repo


def get_repository_with_provider(repo_type: Type = None, provider_type: IDatabase = None) -> Callable:
    def _get_repo():
        return repo_type(provider_type())
    return _get_repo


def get_loader(loader_type: IPriceListLoader) -> Callable:
    def _get_loader():
        return loader_type()
    return _get_loader
