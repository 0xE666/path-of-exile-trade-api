from __future__ import annotations
import json
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

class DiskCache:
    def __init__(self, cache_dir: Path | str, ttl: timedelta):
        self._dir = Path(cache_dir).expanduser()
        self._ttl = ttl

    async def get(self, key: str) -> dict | None:
        path = self._dir / f"{key}.json"
        if not path.exists():
            return None
        def _read():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        try:
            envelope = await asyncio.get_event_loop().run_in_executor(None, _read)
        except (json.JSONDecodeError, OSError):
            return None
        timestamp = datetime.fromisoformat(envelope.get("timestamp", "2000-01-01T00:00:00+00:00"))
        now = datetime.now(timezone.utc)
        if now - timestamp > self._ttl:
            return None
        return envelope.get("data")

    async def set(self, key: str, data: Any) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{key}.json"
        envelope = {"timestamp": datetime.now(timezone.utc).isoformat(), "data": data}
        def _write():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(envelope, f)
        await asyncio.get_event_loop().run_in_executor(None, _write)

    async def clear(self) -> None:
        if not self._dir.exists():
            return
        def _clear():
            for f in self._dir.glob("*.json"):
                f.unlink()
        await asyncio.get_event_loop().run_in_executor(None, _clear)
