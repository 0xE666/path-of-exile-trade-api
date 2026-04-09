from __future__ import annotations
from pydantic import BaseModel

class Price(BaseModel):
    type: str  # "~price" or "~b/o"
    amount: float
    currency: str

class AccountInfo(BaseModel):
    name: str
    online: dict | bool | None = None
    lastCharacterName: str | None = None
    language: str | None = None
    realm: str | None = None

class Listing(BaseModel):
    method: str | None = None
    indexed: str
    stash: dict | None = None
    price: Price | None = None
    account: AccountInfo
    whisper: str | None = None

class SocketInfo(BaseModel):
    group: int
    attr: str | None = None
    sColour: str | None = None

class ItemProperty(BaseModel):
    name: str
    values: list = []
    displayMode: int = 0
    type: int | None = None

class ItemData(BaseModel):
    verified: bool = False
    w: int | None = None
    h: int | None = None
    icon: str | None = None
    league: str | None = None
    id: str
    name: str | None = None
    typeLine: str | None = None
    baseType: str | None = None
    rarity: str | None = None
    ilvl: int | None = None
    identified: bool = True
    corrupted: bool = False
    sockets: list[SocketInfo] = []
    properties: list[ItemProperty] = []
    requirements: list[ItemProperty] = []
    implicitMods: list[str] = []
    explicitMods: list[str] = []
    craftedMods: list[str] = []
    enchantMods: list[str] = []
    fracturedMods: list[str] = []
    flavourText: list[str] = []
    frameType: int | None = None
    note: str | None = None
    extended: dict | None = None

class FetchResult(BaseModel):
    id: str
    listing: Listing
    item: ItemData
