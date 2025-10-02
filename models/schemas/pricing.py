from __future__ import annotations
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator


@dataclass(frozen=True)
class PriceEntry:
    prefix: str = ""
    operator: str = ""
    price: float = 0


class PhoneNumberIn(BaseModel):
    phone_number: str

    @field_validator("phone_number", mode="before")
    def normalize_number(cls, v: str) -> str:
        return v.replace("+", "").replace("-", "")


class CheapestOut(BaseModel):
    operator: str
    price: float
    prefix: str
