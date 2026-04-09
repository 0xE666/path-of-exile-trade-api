from __future__ import annotations
from pydantic import BaseModel
from .common import StatusOption
from .fetch import AccountInfo

class ExchangeQuery(BaseModel):
    status: StatusOption = StatusOption(option="online")
    have: list[str]
    want: list[str]
    minimum: int | None = None
    fulfillable: bool | None = None

class ExchangeRequest(BaseModel):
    engine: str = "new"
    query: ExchangeQuery
    sort: dict = {"have": "asc"}

class OfferItem(BaseModel):
    currency: str
    amount: float
    stock: int | None = None
    id: str | None = None
    whisper: str | None = None

class Offer(BaseModel):
    exchange: OfferItem
    item: OfferItem

class ExchangeListing(BaseModel):
    indexed: str
    account: AccountInfo
    offers: list[Offer] = []
    whisper: str | None = None

class ExchangeResult(BaseModel):
    id: str
    item: dict | None = None
    listing: ExchangeListing

class ExchangeResponse(BaseModel):
    id: str
    complexity: int | None = 0
    result: dict[str, ExchangeResult] = {}
    total: int = 0
    league: str = ""  # injected by client
