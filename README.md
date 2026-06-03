# poetrade

Complete async Python wrapper for the Path of Exile Trade API. Covers both PoE 1 and PoE 2.

## Features

- **100% endpoint coverage** — search, fetch, bulk exchange, whisper, ignore list, live search (WebSocket)
- **PoE 1 + PoE 2** — same interface, pass `game="poe1"` or `game="poe2"`
- **Typed models** — full Pydantic models for every request and response
- **Automatic rate limiting** — parses API response headers, sleeps before hitting limits
- **Disk cache** — static data (stats, items, currencies) cached locally with configurable TTL
- **Query builder** — fluent API for constructing searches without hand-writing JSON
- **PoB build pricer** — feed a pobb.in link, get trade links for every item with tiered mod matching

## Install

```bash
pip install aiohttp pydantic
```

No other dependencies. Drop the `poetrade/` folder into your project.

## Quick Start

```python
import asyncio
from poetrade import TradeClient, QueryBuilder

async def main():
    async with TradeClient(game="poe1", poesessid="your_session_id") as client:
        # Search for an item
        query = (
            QueryBuilder()
            .name("Mageblood")
            .filter("type_filters", rarity="unique")
            .sort("price", "asc")
            .build()
        )
        result = await client.search("Mirage", query)
        items = await client.fetch(result, limit=3)

        print(f"{result.total} listings")
        print(client.trade_url(result))  # clickable trade link

        for item in items:
            p = item.listing.price
            print(f"  {p.amount} {p.currency}")

asyncio.run(main())
```

## Search by Mods

```python
query = (
    QueryBuilder()
    .stat("pseudo.pseudo_total_life", min=80)
    .stat("pseudo.pseudo_total_elemental_resistance", min=100)
    .filter("type_filters", category="accessory.ring", rarity="rare")
    .filter("armour_filters", es_min=200)
    .filter("misc_filters", corrupted=False)
    .filter("trade_filters", price_max=10, price_currency="divine")
    .sort("price", "asc")
    .build()
)
```

### Stat Groups

```python
# "At least 2 of these 3 resistance mods with 30%+"
query = (
    QueryBuilder()
    .stat_group("count", min_match=2, filters=[
        StatFilter(id="explicit.stat_3372524247", value=Range(min=30)),  # fire
        StatFilter(id="explicit.stat_4220027924", value=Range(min=30)),  # cold
        StatFilter(id="explicit.stat_1671376347", value=Range(min=30)),  # lightning
    ])
    .build()
)
```

### Weighted Search

```python
query = (
    QueryBuilder()
    .stat_group("weight", min_weight=100, filters=[
        StatFilter(id="explicit.stat_xxx", value=Range(min=1)),  # weight=1
        StatFilter(id="explicit.stat_yyy", value=Range(min=2)),  # weight=2
    ])
    .build()
)
```

## Currency Exchange

```python
result = await client.exchange("Mirage", have=["chaos"], want=["divine"])
print(client.exchange_url(result))

for _, entry in list(result.result.items())[:3]:
    offer = entry.listing.offers[0]
    ratio = offer.exchange.amount / offer.item.amount
    print(f"  {ratio:.0f} chaos per divine (stock: {offer.item.stock})")
```

## Static Data

```python
leagues = await client.get_leagues()    # available leagues
stats   = await client.get_stats()      # 15K+ searchable stat IDs
items   = await client.get_items()      # all item bases
static  = await client.get_static()     # currency IDs for exchange
filters = await client.get_filters()    # all filter definitions

# Find a stat ID
for cat in stats:
    for entry in cat.entries:
        if "maximum Life" in entry.text and cat.id == "pseudo":
            print(entry.id)  # pseudo.pseudo_total_life
```

All static data is cached to `~/.poetrade/cache/` by default (24h TTL). Pass `cache_dir=None` to disable.

## PoB Build Pricer

Feed a pobb.in link, get pricing for every equipped item with tiered fallback:

```python
from poetrade.pob_pricer import price_build

results = await price_build(
    "https://pobb.in/eCoQERBZqBpY",
    client,
    league="Mirage",
    fetch_count=3,
)

for r in results:
    price = "-"
    if r.cheapest and r.cheapest[0].listing.price:
        p = r.cheapest[0].listing.price
        price = f"{p.amount} {p.currency}"
    print(f"[{r.item.slot}] {r.item.name} — {price} [{r.tier_label}]")
    print(f"  {r.trade_url}")
```

For rare items, the pricer searches by exact mods starting at 90% of roll values. If no results, it falls back through tiers:

| Tier | Min Roll | Use Case |
|------|----------|----------|
| T1 | 90% | Near-perfect rolls |
| T2 | 75% | High-end rolls |
| T3 | 60% | Mid rolls |
| T4 | 45% | Budget rolls |
| Budget | 30% | Anything usable |

## PoE 2

Same interface, different game:

```python
async with TradeClient(game="poe2") as client:
    leagues = await client.get_leagues()  # Fate of the Vaal, etc.
    result = await client.search("Fate of the Vaal", query)
    print(client.trade_url(result))  # https://www.pathofexile.com/trade2/search/...
```

## Authentication

`POESESSID` is optional but recommended. Without it you get IP-only rate limits. With it you get account-level limits too (roughly 2x capacity).

Find your POESESSID:
1. Log into pathofexile.com
2. Open browser dev tools → Application → Cookies
3. Copy the `POESESSID` value

## Rate Limits

The wrapper handles rate limits automatically. It parses `X-Rate-Limit-*` headers from every response and sleeps before requests when approaching limits. On 429 (rate limited), it reads `Retry-After` and retries up to 3 times.

| Endpoint | Limits |
|----------|--------|
| Search | 5/10s, 15/60s, 30/300s |
| Fetch | 12/4s, 16/12s |
| Exchange | 5/15s, 10/90s, 30/300s |

## API Reference

### TradeClient

```python
TradeClient(
    game="poe1",           # "poe1" or "poe2"
    poesessid=None,        # optional session cookie
    user_agent="...",      # User-Agent header
    cache_dir="~/.poetrade/cache",  # None to disable
    cache_ttl=timedelta(hours=24),
)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `search(league, request)` | `SearchResponse` | Search for items |
| `fetch(result, limit=None)` | `list[FetchResult]` | Fetch item details (auto-batches by 10) |
| `exchange(league, have, want)` | `ExchangeResponse` | Bulk currency exchange |
| `trade_url(result)` | `str` | Browser trade URL |
| `exchange_url(result)` | `str` | Browser exchange URL |
| `get_leagues()` | `list[League]` | Available leagues |
| `get_stats()` | `list[StatCategory]` | All stat filter IDs |
| `get_items()` | `list[ItemCategory]` | All item bases |
| `get_static()` | `list[StaticCategory]` | Currency IDs |
| `get_filters()` | `dict` | Filter definitions |
| `whisper(whisper_token)` | `str` | Direct Whisper a seller (pass `listing.whisper_token`; needs same league). For a copy-paste message use `listing.whisper`. |
| `get_ignored()` | `list[dict]` | Ignored accounts |
| `ignore_account(name)` | `None` | Ignore an account |
| `unignore_account(name)` | `None` | Unignore |
| `live_search(league, id)` | `AsyncIterator` | WebSocket live results |
| `clear_cache()` | `None` | Clear disk cache |

### QueryBuilder

| Method | Description |
|--------|-------------|
| `.name("Headhunter")` | Item name (unique) |
| `.type("Leather Belt")` | Base type |
| `.term("search text")` | Free-text search |
| `.status("online")` | online / any |
| `.stat(id, min, max)` | Add stat filter to default AND group |
| `.stat_group(type, filters, ...)` | count / weight / not group |
| `.filter(group, **kwargs)` | Add filter (type, armour, misc, trade, etc.) |
| `.sort(key, direction)` | Sort by price asc/desc |
| `.build()` | Returns `SearchRequest` |

### Filter kwargs

```python
# Options
.filter("type_filters", category="armour.chest", rarity="unique")

# Ranges (use _min / _max suffix)
.filter("armour_filters", es_min=300, es_max=500)

# Booleans
.filter("misc_filters", corrupted=False, fractured_item=True)

# Price (special compound)
.filter("trade_filters", price_min=1, price_max=100, price_currency="chaos")

# Time listed
.filter("trade_filters", indexed="1week")
```

## License

Do whatever you want with it.
