from __future__ import annotations
import asyncio
from aiohttp import ClientSession
from ..exceptions import InvalidQueryError, ServerError, RateLimitError, AuthenticationError
from ..rate_limiter import RateLimiter
from ..models.search import SearchRequest, SearchResponse

BASE = "https://www.pathofexile.com"
POLICY = "trade-search-request-limit"
MAX_RETRIES = 3

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def search(session: ClientSession, game: str, league: str, request: SearchRequest, limiter: RateLimiter) -> SearchResponse:
    url = f"{BASE}/api/{_api_prefix(game)}/search/{league}"
    body = request.model_dump(exclude_none=True)
    for attempt in range(MAX_RETRIES):
        await limiter.acquire(POLICY)
        resp = await session.post(url, json=body)
        policy = resp.headers.get("X-Rate-Limit-Policy", POLICY)
        limiter.update(policy, resp.headers)
        if resp.status == 200:
            data = await resp.json()
            return SearchResponse(**data, league=league)
        elif resp.status == 429:
            wait = limiter.handle_429(resp.headers)
            await asyncio.sleep(wait)
            continue
        elif resp.status in (401, 403):
            raise AuthenticationError(status_code=resp.status)
        elif resp.status == 400:
            data = await resp.json()
            raise InvalidQueryError(message=data.get("error", {}).get("message", "Bad request"), status_code=400, body=data)
        else:
            raise ServerError(message=f"Server error: {resp.status}", status_code=resp.status)
    raise RateLimitError("Rate limited after max retries", retry_after=60.0)
