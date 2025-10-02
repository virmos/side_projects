from typing import Type, Callable
from models.db.types import IDatabase


def get_repository_with_provider(repo_type: Type = None, provider_type: IDatabase = None) -> Callable:
    def _get_repo():
        return repo_type(provider_type())
    return _get_repo

