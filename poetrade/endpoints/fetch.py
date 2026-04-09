from __future__ import annotations
import asyncio
from aiohttp import ClientSession
from ..exceptions import ServerError, RateLimitError
from ..rate_limiter import RateLimiter
from ..helpers import batch_hashes
from ..models.fetch import FetchResult

BASE = "https://www.pathofexile.com"
POLICY = "trade-fetch-request-limit"
BATCH_SIZE = 10
MAX_RETRIES = 3

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def fetch(session: ClientSession, game: str, hashes: list[str], query_id: str, limiter: RateLimiter, limit: int | None = None) -> list[FetchResult]:
    if limit is not None:
        hashes = hashes[:limit]
    results: list[FetchResult] = []
    for batch in batch_hashes(hashes, BATCH_SIZE):
        items_str = ",".join(batch)
        url = f"{BASE}/api/{_api_prefix(game)}/fetch/{items_str}?query={query_id}"
        for attempt in range(MAX_RETRIES):
            await limiter.acquire(POLICY)
            resp = await session.get(url)
            policy = resp.headers.get("X-Rate-Limit-Policy", POLICY)
            limiter.update(policy, resp.headers)
            if resp.status == 200:
                data = await resp.json()
                for item_data in data.get("result", []):
                    if item_data is not None:
                        results.append(FetchResult(**item_data))
                break
            elif resp.status == 429:
                wait = limiter.handle_429(resp.headers)
                await asyncio.sleep(wait)
                continue
            else:
                raise ServerError(message=f"Fetch error: {resp.status}", status_code=resp.status)
        else:
            raise RateLimitError("Rate limited after max retries", retry_after=60.0)
    return results
