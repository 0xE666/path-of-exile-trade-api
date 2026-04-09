from __future__ import annotations
from pydantic import BaseModel

class League(BaseModel):
    id: str
    realm: str
    text: str

class StatOption(BaseModel):
    id: int
    text: str

class StatEntry(BaseModel):
    id: str
    text: str
    type: str
    option: dict | None = None

class StatCategory(BaseModel):
    id: str
    label: str
    entries: list[StatEntry] = []

class ItemEntry(BaseModel):
    type: str
    name: str | None = None
    text: str | None = None
    flags: dict | None = None

class ItemCategory(BaseModel):
    id: str
    label: str
    entries: list[ItemEntry] = []

class StaticEntry(BaseModel):
    id: str
    text: str
    image: str | None = None

class StaticCategory(BaseModel):
    id: str
    label: str | None = None
    entries: list[StaticEntry] = []
