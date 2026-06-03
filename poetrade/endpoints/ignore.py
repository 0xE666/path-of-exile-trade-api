from __future__ import annotations
from urllib.parse import quote
from aiohttp import ClientSession
from ..exceptions import AuthenticationError, ServerError

BASE = "https://www.pathofexile.com"

def _api_prefix(game: str) -> str:
    return "trade" if game == "poe1" else "trade2"

async def get_ignored(session: ClientSession, game: str) -> list[dict]:
    url = f"{BASE}/api/{_api_prefix(game)}/ignore"
    resp = await session.get(url)
    if resp.status == 200:
        data = await resp.json()
        return data.get("result", [])
    elif resp.status in (401, 403):
        raise AuthenticationError(status_code=resp.status)
    else:
        raise ServerError(message=f"Ignore list error: {resp.status}", status_code=resp.status)

async def ignore_account(session: ClientSession, game: str, account: str) -> None:
    # Account names include a "#1234" discriminator (and may contain spaces);
    # the segment must be percent-encoded or the API 404s.
    url = f"{BASE}/api/{_api_prefix(game)}/ignore/{quote(account, safe='')}"
    resp = await session.put(url)
    if resp.status in (401, 403):
        raise AuthenticationError(status_code=resp.status)
    elif resp.status >= 400:
        raise ServerError(message=f"Ignore error: {resp.status}", status_code=resp.status)

async def unignore_account(session: ClientSession, game: str, account: str) -> None:
    url = f"{BASE}/api/{_api_prefix(game)}/ignore/{quote(account, safe='')}"
    resp = await session.delete(url)
    if resp.status in (401, 403):
        raise AuthenticationError(status_code=resp.status)
    elif resp.status >= 400:
        raise ServerError(message=f"Unignore error: {resp.status}", status_code=resp.status)
