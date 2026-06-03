# Changelog

## [Unreleased] — PoE 2 verification & fixes

Verified the wrapper end-to-end against the live trade API for both games and
fixed several bugs uncovered in the process. All data endpoints remain dynamic
(stats/items/currencies are fetched live), so no static data needed updating.

### Fixed
- **Browser URLs missing the PoE 2 realm segment.** `trade_url()` / `exchange_url()`
  now emit `/trade2/search/poe2/<league>/<id>` for PoE 2 (was `/trade2/search/<league>/<id>`,
  producing dead links). PoE 1 URLs are unchanged.
- **League names with spaces produced malformed URLs.** League segments in
  `trade_url()` / `exchange_url()` are now percent-encoded (e.g. `Runes of Aldur`
  → `Runes%20of%20Aldur`).
- **`ignore_account()` / `unignore_account()` always 404'd.** Account names carry a
  `#1234` discriminator; the unescaped `#` truncated the request path. The account
  segment is now percent-encoded.
- **`whisper()` was broken.** It POSTed `{"id": <listing hash>}` and lacked the
  headers the endpoint requires. It now sends `{"token": <whisper_token>}` with the
  required `Origin` / `X-Requested-With` headers, and the new `Listing.whisper_token`
  field exposes the token. `whisper()` now takes a `whisper_token` argument. For a
  copy-paste message without triggering an in-game whisper, use `listing.whisper`.
- **`whisper()` now surfaces the API error message** (e.g. "You must be in the same
  league as the seller") as `InvalidQueryError` instead of a generic `ServerError`.
- **PoB pricer missed PoE 2 gear slots.** `extract_items()` now recognizes PoE 2's
  third ring (`Ring 3`) and charm slots (`Charm 1..3`) in addition to the PoE 1 slots.

### Changed
- `TradeClient` now sends `Origin` and `X-Requested-With` headers on every request
  (required for the live-search WebSocket handshake and the Direct Whisper endpoint).

### Removed
- Deleted the broken, unused top-level `models/` package (a duplicate of
  `poetrade/models/` that could not be imported).

### Verified against live API
- PoE 2: `leagues`, `stats` (7.2k entries), `items` (3.7k bases), `static`, `filters`,
  `search` → `fetch` → `exchange`, `get_ignored`, `ignore`/`unignore` (round-trip),
  `whisper` (reaches the same-league game check), `live_search` (WebSocket connects),
  and the PoB pricer slot/mod-matching logic.
- PoE 1: `search` → `fetch` → `exchange` and URL generation.
