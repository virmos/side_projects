from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings
from decouple import config as decouple_config


Environment = Literal["DEV", "STAGING", "PROD"]


class BackendBaseSettings(BaseSettings):
    TITLE: str = decouple_config("TITLE", cast=str)
    VERSION: str = decouple_config("VERSION", cast=str)
    TIMEZONE: str = decouple_config("TIMEZONE", cast=str)
    DESCRIPTION: str = decouple_config("DESCRIPTION", cast=str)
    DEBUG: bool = decouple_config("DEBUG", cast=bool)
    TEST_PRICING_DB: str = decouple_config("TEST_PRICING_DB", default="", cast=str)
    PROD_PRICING_DB: str = decouple_config("PROD_PRICING_DB", default="", cast=str)
    USE_TEST_DB: bool = decouple_config("USE_TEST_DB", default="", cast=bool)
    USE_DB_FAST_LOAD: bool = decouple_config("USE_DB_FAST_LOAD", default="", cast=bool)


class BackendDevSettings(BackendBaseSettings):
    DEBUG: bool = True


class BackendStageSettings(BackendBaseSettings):
    pass


class BackendProdSettings(BackendBaseSettings):
    pass


class BackendSettingsFactory:
    def __init__(self, environment: str):
        self.environment = environment

    def __call__(self) -> BackendBaseSettings:
        if self.environment.upper() == "DEV":
            return BackendDevSettings()
        if self.environment.upper() == "STAGING":
            return BackendStageSettings()
        return BackendProdSettings()


@lru_cache()
def get_settings() -> BackendBaseSettings:
    return BackendSettingsFactory(
        environment=decouple_config("ENVIRONMENT", default="DEV", cast=str)
    )()


settings: BackendBaseSettings = get_settings()


