from __future__ import annotations


class TradeAPIError(Exception):
    """Base exception for trade API errors."""

    def __init__(self, message: str, status_code: int = 0, body: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.body = body or {}
        super().__init__(message)


class RateLimitError(TradeAPIError):
    """429 after max retries exhausted."""

    def __init__(self, message: str, retry_after: float, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, **kwargs)


class AuthenticationError(TradeAPIError):
    """401/403 — POESESSID missing or invalid."""

    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, **kwargs)


class InvalidQueryError(TradeAPIError):
    """400 — bad stat ID, unknown filter, malformed query."""
    pass


class ServerError(TradeAPIError):
    """500/502/503 from GGG servers."""
    pass
