from __future__ import annotations
from typing import Iterator, Sequence, TypeVar

T = TypeVar("T")
BASE_URL = "https://www.pathofexile.com"

def _prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

def trade_url(game: str, league: str, query_id: str) -> str:
    return f"{BASE_URL}/{_prefix(game)}/search/{league}/{query_id}"

def exchange_url(game: str, league: str, query_id: str) -> str:
    return f"{BASE_URL}/{_prefix(game)}/exchange/{league}/{query_id}"

def batch_hashes(items: Sequence[T], batch_size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), batch_size):
        yield list(items[i : i + batch_size])
