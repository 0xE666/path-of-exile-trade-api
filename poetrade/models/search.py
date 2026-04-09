from __future__ import annotations
from pydantic import BaseModel
from .common import Range, StatusOption, SortOption

class StatFilter(BaseModel):
    id: str
    value: Range | None = None
    disabled: bool = False

class StatGroup(BaseModel):
    type: str  # "and" | "not" | "count" | "weight" | "if"
    filters: list[StatFilter] = []
    value: Range | None = None
    disabled: bool = False

class Filters(BaseModel):
    type_filters: dict | None = None
    weapon_filters: dict | None = None
    armour_filters: dict | None = None
    equipment_filters: dict | None = None  # PoE 2
    socket_filters: dict | None = None
    req_filters: dict | None = None
    map_filters: dict | None = None
    heist_filters: dict | None = None
    sanctum_filters: dict | None = None
    ultimatum_filters: dict | None = None
    misc_filters: dict | None = None
    trade_filters: dict | None = None

class SearchQuery(BaseModel):
    status: StatusOption = StatusOption(option="any")
    name: str | dict | None = None
    type: str | dict | None = None
    term: str | None = None
    stats: list[StatGroup] = []
    filters: Filters = Filters()

class SearchRequest(BaseModel):
    query: SearchQuery
    sort: SortOption = SortOption(price="asc")

class SearchResponse(BaseModel):
    id: str
    complexity: int = 0
    result: list[str] = []
    total: int = 0
    inexact: bool = False
    league: str = ""  # injected by client
