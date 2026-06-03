from __future__ import annotations
from aiohttp import ClientSession
from ..exceptions import AuthenticationError, InvalidQueryError, ServerError
from ..rate_limiter import RateLimiter

BASE = "https://www.pathofexile.com"

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def whisper(session: ClientSession, game: str, whisper_token: str, limiter: RateLimiter) -> str:
    """Trigger a Direct Whisper. Pass the listing's ``whisper_token`` (from a
    fetched ``Listing``), not the listing hash. Requires an authenticated
    session in the same league as the seller. For a copy-paste message without
    triggering an in-game whisper, use ``listing.whisper`` instead."""
    url = f"{BASE}/api/{_api_prefix(game)}/whisper"
    resp = await session.post(url, json={"token": whisper_token})
    if resp.status == 200:
        data = await resp.json()
        return data.get("result", {}).get("whisper", "")
    elif resp.status in (401, 403):
        raise AuthenticationError(status_code=resp.status)
    elif resp.status == 400:
        data = await resp.json()
        raise InvalidQueryError(
            message=data.get("error", {}).get("message", "Bad whisper request"),
            status_code=400,
            body=data,
        )
    else:
        raise ServerError(message=f"Whisper error: {resp.status}", status_code=resp.status)
