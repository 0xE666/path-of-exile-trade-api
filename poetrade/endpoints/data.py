from __future__ import annotations
from aiohttp import ClientSession
from ..cache import DiskCache
from ..rate_limiter import RateLimiter
from ..models.data import League, StatCategory, ItemCategory, StaticCategory

BASE = "https://www.pathofexile.com"

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def _get_cached(session: ClientSession, game: str, endpoint: str, limiter: RateLimiter, cache: DiskCache | None) -> dict:
    cache_key = f"{game}_{endpoint}"
    if cache:
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
    url = f"{BASE}/api/{_api_prefix(game)}/data/{endpoint}"
    await limiter.acquire("trade-fetch-request-limit")
    resp = await session.get(url)
    policy = resp.headers.get("X-Rate-Limit-Policy", "")
    if policy:
        limiter.update(policy, resp.headers)
    data = await resp.json()
    if cache:
        await cache.set(cache_key, data)
    return data

async def get_leagues(session, game, limiter, cache) -> list[League]:
    data = await _get_cached(session, game, "leagues", limiter, cache)
    return [League(**e) for e in data.get("result", [])]

async def get_stats(session, game, limiter, cache) -> list[StatCategory]:
    data = await _get_cached(session, game, "stats", limiter, cache)
    return [StatCategory(**e) for e in data.get("result", [])]

async def get_items(session, game, limiter, cache) -> list[ItemCategory]:
    data = await _get_cached(session, game, "items", limiter, cache)
    return [ItemCategory(**e) for e in data.get("result", [])]

async def get_static(session, game, limiter, cache) -> list[StaticCategory]:
    data = await _get_cached(session, game, "static", limiter, cache)
    return [StaticCategory(**e) for e in data.get("result", [])]

async def get_filters(session, game, limiter, cache) -> dict:
    data = await _get_cached(session, game, "filters", limiter, cache)
    return data.get("result", {})
