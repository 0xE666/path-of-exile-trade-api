from __future__ import annotations
from pydantic import BaseModel

class Range(BaseModel):
    min: float | None = None
    max: float | None = None

class StatusOption(BaseModel):
    option: str  # "online" | "onlineleague" | "any"

class SortOption(BaseModel):
    price: str | None = None  # "asc" | "desc"
    have: str | None = None   # for exchange sort
