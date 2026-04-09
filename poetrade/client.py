from __future__ import annotations
from datetime import timedelta
from pathlib import Path
from typing import AsyncIterator
import aiohttp
from .cache import DiskCache
from .rate_limiter import RateLimiter
from .helpers import trade_url as _trade_url, exchange_url as _exchange_url
from .models.search import SearchRequest, SearchResponse
from .models.fetch import FetchResult
from .models.exchange import ExchangeResponse
from .models.data import League, StatCategory, ItemCategory, StaticCategory
from .endpoints import data as data_ep
from .endpoints import search as search_ep
from .endpoints import fetch as fetch_ep
from .endpoints import exchange as exchange_ep
from .endpoints import whisper as whisper_ep
from .endpoints import ignore as ignore_ep
from .endpoints import live as live_ep


class TradeClient:
    def __init__(
        self,
        game: str = "poe1",
        poesessid: str | None = None,
        user_agent: str = "poetrade-python/1.0",
        cache_dir: str | Path | None = "~/.poetrade/cache",
        cache_ttl: timedelta = timedelta(hours=24),
    ):
        self.game = game
        self._poesessid = poesessid
        self._user_agent = user_agent
        self._limiter = RateLimiter()
        self._session: aiohttp.ClientSession | None = None
        if cache_dir is not None:
            self._cache: DiskCache | None = DiskCache(
                cache_dir=cache_dir, ttl=cache_ttl
            )
        else:
            self._cache = None

    async def __aenter__(self) -> TradeClient:
        headers = {"User-Agent": self._user_agent}
        cookies = {}
        if self._poesessid:
            cookies["POESESSID"] = self._poesessid
        self._session = aiohttp.ClientSession(headers=headers, cookies=cookies)
        return self

    async def __aexit__(self, *args) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def _s(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("TradeClient must be used as async context manager")
        return self._session

    async def get_leagues(self) -> list[League]:
        return await data_ep.get_leagues(self._s, self.game, self._limiter, self._cache)

    async def get_stats(self) -> list[StatCategory]:
        return await data_ep.get_stats(self._s, self.game, self._limiter, self._cache)

    async def get_items(self) -> list[ItemCategory]:
        return await data_ep.get_items(self._s, self.game, self._limiter, self._cache)

    async def get_static(self) -> list[StaticCategory]:
        return await data_ep.get_static(self._s, self.game, self._limiter, self._cache)

    async def get_filters(self) -> dict:
        return await data_ep.get_filters(self._s, self.game, self._limiter, self._cache)

    async def clear_cache(self) -> None:
        if self._cache:
            await self._cache.clear()

    async def search(self, league: str, request: SearchRequest) -> SearchResponse:
        return await search_ep.search(
            self._s, self.game, league, request, self._limiter
        )

    def trade_url(self, result: SearchResponse) -> str:
        return _trade_url(self.game, result.league, result.id)

    async def fetch(
        self, result: SearchResponse, *, limit: int | None = None
    ) -> list[FetchResult]:
        return await fetch_ep.fetch(
            self._s, self.game, result.result, result.id, self._limiter, limit=limit
        )

    async def exchange(
        self,
        league: str,
        *,
        have: list[str],
        want: list[str],
        minimum: int | None = None,
        status: str = "online",
    ) -> ExchangeResponse:
        return await exchange_ep.exchange(
            self._s,
            self.game,
            league,
            have,
            want,
            self._limiter,
            minimum=minimum,
            status=status,
        )

    def exchange_url(self, result: ExchangeResponse) -> str:
        return _exchange_url(self.game, result.league, result.id)

    async def whisper(self, listing_id: str) -> str:
        return await whisper_ep.whisper(
            self._s, self.game, listing_id, self._limiter
        )

    async def get_ignored(self) -> list[dict]:
        return await ignore_ep.get_ignored(self._s, self.game)

    async def ignore_account(self, account: str) -> None:
        await ignore_ep.ignore_account(self._s, self.game, account)

    async def unignore_account(self, account: str) -> None:
        await ignore_ep.unignore_account(self._s, self.game, account)

    async def live_search(
        self, league: str, query_id: str
    ) -> AsyncIterator[list[FetchResult]]:
        async for results in live_ep.live_search(
            self._s, self.game, league, query_id, self._limiter
        ):
            yield results
