from __future__ import annotations
from aiohttp import ClientSession
from ..exceptions import AuthenticationError, ServerError
from ..rate_limiter import RateLimiter

BASE = "https://www.pathofexile.com"

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def whisper(session: ClientSession, game: str, listing_id: str, limiter: RateLimiter) -> str:
    url = f"{BASE}/api/{_api_prefix(game)}/whisper"
    resp = await session.post(url, json={"id": listing_id})
    if resp.status == 200:
        data = await resp.json()
        return data.get("result", {}).get("whisper", "")
    elif resp.status in (401, 403):
        raise AuthenticationError(status_code=resp.status)
    else:
        raise ServerError(message=f"Whisper error: {resp.status}", status_code=resp.status)
