from __future__ import annotations
import json
from typing import AsyncIterator
from aiohttp import ClientSession
from ..rate_limiter import RateLimiter
from ..models.fetch import FetchResult
from .fetch import fetch

BASE = "wss://www.pathofexile.com"

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def live_search(session: ClientSession, game: str, league: str, query_id: str, limiter: RateLimiter) -> AsyncIterator[list[FetchResult]]:
    url = f"{BASE}/api/{_api_prefix(game)}/live/{league}/{query_id}"
    async with session.ws_connect(url) as ws:
        async for msg in ws:
            if msg.data is None:
                continue
            try:
                data = json.loads(msg.data) if isinstance(msg.data, str) else msg.data
            except (json.JSONDecodeError, TypeError):
                continue
            new_hashes = data.get("new", [])
            if new_hashes:
                results = await fetch(session, game, new_hashes, query_id, limiter)
                yield results
