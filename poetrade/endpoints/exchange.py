from __future__ import annotations
import asyncio
from aiohttp import ClientSession
from ..exceptions import InvalidQueryError, ServerError, RateLimitError, AuthenticationError
from ..rate_limiter import RateLimiter
from ..models.common import StatusOption
from ..models.exchange import ExchangeQuery, ExchangeRequest, ExchangeResponse

BASE = "https://www.pathofexile.com"
POLICY = "trade-exchange-request-limit"
MAX_RETRIES = 3

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def exchange(session: ClientSession, game: str, league: str, have: list[str], want: list[str], limiter: RateLimiter, *, minimum: int | None = None, status: str = "online") -> ExchangeResponse:
    url = f"{BASE}/api/{_api_prefix(game)}/exchange/{league}"
    req = ExchangeRequest(query=ExchangeQuery(status=StatusOption(option=status), have=have, want=want, minimum=minimum))
    body = req.model_dump(exclude_none=True)
    for attempt in range(MAX_RETRIES):
        await limiter.acquire(POLICY)
        resp = await session.post(url, json=body)
        policy = resp.headers.get("X-Rate-Limit-Policy", POLICY)
        limiter.update(policy, resp.headers)
        if resp.status == 200:
            data = await resp.json()
            return ExchangeResponse(**data, league=league)
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
            raise ServerError(message=f"Exchange error: {resp.status}", status_code=resp.status)
    raise RateLimitError("Rate limited after max retries", retry_after=60.0)
