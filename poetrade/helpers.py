from __future__ import annotations
from typing import Iterator, Sequence, TypeVar
from urllib.parse import quote

T = TypeVar("T")
BASE_URL = "https://www.pathofexile.com"

def _prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

def _realm_segment(game: str) -> str:
    # PoE 2 browser trade URLs carry a "poe2" realm segment in the path
    # (e.g. /trade2/search/poe2/Standard/<id>); PoE 1 omits it.
    return "poe2/" if game == "poe2" else ""

def trade_url(game: str, league: str, query_id: str) -> str:
    league = quote(league, safe="")  # league names contain spaces (e.g. "Runes of Aldur")
    return f"{BASE_URL}/{_prefix(game)}/search/{_realm_segment(game)}{league}/{query_id}"

def exchange_url(game: str, league: str, query_id: str) -> str:
    league = quote(league, safe="")
    return f"{BASE_URL}/{_prefix(game)}/exchange/{_realm_segment(game)}{league}/{query_id}"

def batch_hashes(items: Sequence[T], batch_size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), batch_size):
        yield list(items[i : i + batch_size])
