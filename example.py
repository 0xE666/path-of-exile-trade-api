"""
poetrade - Complete Python wrapper for the PoE Trade API (PoE 1 + PoE 2)

pip install aiohttp pydantic

Usage: Set your POESESSID below and run this file.
       python example.py
"""
import asyncio
from poetrade import TradeClient, QueryBuilder, StatFilter, Range

# ── Set your session ID here ────────────────────────────────────────
POESESSID = None  # e.g. "abc123def456" — optional but recommended for higher rate limits
LEAGUE = "Mirage"
# ────────────────────────────────────────────────────────────────────


async def example_search_unique():
    """Search for a unique item by name."""
    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        query = (
            QueryBuilder()
            .name("Mageblood")
            .filter("type_filters", rarity="unique")
            .sort("price", "asc")
            .build()
        )
        result = await client.search(LEAGUE, query)
        items = await client.fetch(result, limit=3)

        print(f"Mageblood: {result.total} listings")
        print(f"Trade URL: {client.trade_url(result)}")
        for item in items:
            p = item.listing.price
            print(f"  {p.amount} {p.currency} — {item.listing.account.name}")

    # Example output (Mirage league, Apr 2026):
    # Mageblood: 1642 listings
    # Trade URL: https://www.pathofexile.com/trade/search/Mirage/wvGnpGlrUb
    #   100.0 chaos — seller1#1234
    #   1.0 divine — seller2#5678
    #   1.0 divine — seller3#9012


async def example_search_by_stats():
    """Search for rares with specific mod requirements."""
    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        query = (
            QueryBuilder()
            .stat("pseudo.pseudo_total_life", min=80)
            .stat("pseudo.pseudo_total_elemental_resistance", min=100)
            .filter("type_filters", category="accessory.ring", rarity="rare")
            .filter("trade_filters", price_max=5, price_currency="divine")
            .sort("price", "asc")
            .build()
        )
        result = await client.search(LEAGUE, query)
        items = await client.fetch(result, limit=3)

        print(f"\nLife+Res rings: {result.total} listings")
        print(f"Trade URL: {client.trade_url(result)}")
        for item in items:
            p = item.listing.price
            price = f"{p.amount} {p.currency}" if p else "unpriced"
            print(f"  {item.item.typeLine} — {price}")
            for mod in item.item.explicitMods[:4]:
                print(f"    {mod}")

    # Example output:
    # Life+Res rings: 10000 listings
    # Trade URL: https://www.pathofexile.com/trade/search/Mirage/Z6ZnbpM9HQ
    #   Two-Stone Ring — 0.2 divine
    #     +107 to maximum Life
    #     +39% to Cold Resistance
    #     +38% to Lightning Resistance
    #     14% of Damage taken Recouped as Life
    #   Sapphire Ring — 0.5 divine
    #     +41 to Intelligence
    #     +98 to maximum Life
    #     +65 to maximum Mana
    #     +39% to Cold Resistance


async def example_stat_groups():
    """Use count and weight stat groups for advanced searches."""
    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        # "At least 2 of these 3 resistance mods"
        query = (
            QueryBuilder()
            .stat("pseudo.pseudo_total_life", min=70)
            .stat_group(
                "count",
                min_match=2,
                filters=[
                    StatFilter(id="explicit.stat_3372524247", value=Range(min=30)),  # fire res
                    StatFilter(id="explicit.stat_4220027924", value=Range(min=30)),  # cold res
                    StatFilter(id="explicit.stat_1671376347", value=Range(min=30)),  # lightning res
                ],
            )
            .filter("type_filters", category="armour.gloves", rarity="rare")
            .sort("price", "asc")
            .build()
        )
        result = await client.search(LEAGUE, query)
        print(f"\nDual-res life gloves: {result.total} listings")
        print(f"Trade URL: {client.trade_url(result)}")


async def example_exchange():
    """Currency exchange — check divine orb prices."""
    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        result = await client.exchange(LEAGUE, have=["chaos"], want=["divine"])

        print(f"\nChaos -> Divine: {result.total} sellers")
        print(f"Exchange URL: {client.exchange_url(result)}")
        for _, entry in list(result.result.items())[:3]:
            offer = entry.listing.offers[0]
            ratio = offer.exchange.amount / offer.item.amount
            print(f"  {ratio:.0f} chaos per divine (stock: {offer.item.stock})")

    # Example output:
    # Chaos -> Divine: 9 sellers
    # Exchange URL: https://www.pathofexile.com/trade/exchange/Mirage/9z28fK
    #   330 chaos per divine (stock: 1)
    #   350 chaos per divine (stock: 5)


async def example_static_data():
    """Browse available leagues, stats, items, and currencies."""
    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        # Leagues
        leagues = await client.get_leagues()
        print(f"\nLeagues: {[l.id for l in leagues[:6]]}")

        # Stat categories (for building stat filters)
        stats = await client.get_stats()
        print("Stat categories:")
        for cat in stats:
            print(f"  {cat.id}: {cat.label} ({len(cat.entries)} stats)")

        # Search for a stat ID by text
        for cat in stats:
            for entry in cat.entries:
                if "maximum Life" in entry.text and cat.id == "pseudo":
                    print(f"\nFound: {entry.id} = '{entry.text}'")
                    break

    # Example output:
    # Leagues: ['Mirage', 'Hardcore Mirage', 'Ruthless Mirage', 'HC Ruthless Mirage', 'Standard', 'Hardcore']
    # Stat categories:
    #   pseudo: Pseudo (298 stats)
    #   explicit: Explicit (6747 stats)
    #   implicit: Implicit (1428 stats)
    #   fractured: Fractured (1805 stats)
    #   ...
    # Found: pseudo.pseudo_total_life = '+# total maximum Life'


async def example_poe2():
    """PoE 2 uses the same API, just pass game='poe2'."""
    async with TradeClient(game="poe2", poesessid=POESESSID) as client:
        leagues = await client.get_leagues()
        print(f"\nPoE 2 leagues: {[l.id for l in leagues[:4]]}")

        query = (
            QueryBuilder()
            .filter("type_filters", rarity="unique")
            .stat("pseudo.pseudo_total_life", min=50)
            .sort("price", "asc")
            .build()
        )
        result = await client.search(leagues[0].id, query)
        print(f"PoE 2 uniques with 50+ life: {result.total} listings")
        print(f"Trade URL: {client.trade_url(result)}")

    # Example output:
    # PoE 2 leagues: ['Fate of the Vaal', 'HC Fate of the Vaal', 'Standard', 'Hardcore']
    # PoE 2 uniques with 50+ life: 2027 listings
    # Trade URL: https://www.pathofexile.com/trade2/search/Fate of the Vaal/EBdgE0ezC5


async def example_query_builder():
    """QueryBuilder produces a JSON body you can inspect before sending."""
    query = (
        QueryBuilder()
        .name("Headhunter")
        .type("Leather Belt")
        .status("online")
        .stat("pseudo.pseudo_total_life", min=70)
        .filter("type_filters", category="accessory.belt", rarity="unique")
        .filter("trade_filters", price_min=1, price_currency="divine")
        .sort("price", "asc")
        .build()
    )
    print("\nGenerated query JSON:")
    print(query.model_dump_json(exclude_none=True, indent=2))

    # Output:
    # {
    #   "query": {
    #     "status": {"option": "online"},
    #     "name": "Headhunter",
    #     "type": "Leather Belt",
    #     "stats": [{"type": "and", "filters": [
    #       {"id": "pseudo.pseudo_total_life", "value": {"min": 70.0}, "disabled": false}
    #     ], "disabled": false}],
    #     "filters": {
    #       "type_filters": {"filters": {"category": {"option": "accessory.belt"}, "rarity": {"option": "unique"}}},
    #       "trade_filters": {"filters": {"price": {"min": 1, "option": "divine"}}}
    #     }
    #   },
    #   "sort": {"price": "asc"}
    # }


async def example_pob_pricer():
    """Price an entire build from a pobb.in link with tiered fallback."""
    from poetrade.pob_pricer import price_build

    async with TradeClient(game="poe1", poesessid=POESESSID) as client:
        results = await price_build(
            "https://pobb.in/eCoQERBZqBpY",  # Ward Loop Ascendant
            client,
            league=LEAGUE,
            fetch_count=3,
        )

        print(f"\nBuild Pricer: {len(results)} items")
        for r in results:
            if r.error and "Skipped" in r.error:
                continue
            if r.error:
                print(f"  [{r.item.slot}] {r.item.name} — ERROR: {r.error}")
                continue

            price = "-"
            if r.cheapest and r.cheapest[0].listing.price:
                p = r.cheapest[0].listing.price
                price = f"{p.amount} {p.currency}"

            total = r.search_response.total if r.search_response else 0
            tier = f" [{r.tier_label}]" if r.tier_label else ""
            print(f"  [{r.item.slot}] {r.item.name} — {price} ({total} listed){tier}")
            if r.trade_url:
                print(f"    {r.trade_url}")

    # Example output (Mirage league):
    #   [Helmet] Faithguard — 1.0 chaos (1126 listed) [Unique]
    #     https://www.pathofexile.com/trade/search/Mirage/pJEnl7jWS0
    #   [Body Armour] Rift Salvation — - (0 listed) [No matches at any tier]
    #   [Gloves] Morbid Nails — 60.0 divine (8 listed) [T1 (90% rolls)]
    #     https://www.pathofexile.com/trade/search/Mirage/OgnPVgbauE
    #   [Boots] Woe Dash — 23.0 divine (8 listed) [T1 (90% rolls)]
    #   [Weapon 1] Grace of the Goddess — 1.0 chaos (10000 listed) [Unique]
    #   [Ring 1] Foulborn Heartbound Loop — 1.0 chaos (2999 listed) [Unique]
    #   [Amulet] Storm Noose — 26.0 divine (18 listed) [T1 (90% rolls)]
    #   [Belt] Ynda's Stand — 1.0 divine (712 listed) [Unique]
    #   [Flask 4] Starlight Chalice — 28.0 divine (49 listed) [Unique]


# ── Run all examples ────────────────────────────────────────────────

async def main():
    print("=" * 56)
    print("  poetrade — PoE Trade API Wrapper Examples")
    print("=" * 56)

    # This one works without POESESSID
    await example_query_builder()

    if not POESESSID:
        print("\n⚠ Set POESESSID at the top of this file to run live API examples.")
        print("  You can find it in your browser cookies after logging into pathofexile.com")
        return

    await example_search_unique()
    await example_search_by_stats()
    await example_stat_groups()
    await example_exchange()
    await example_static_data()
    await example_poe2()
    await example_pob_pricer()

    print("\n" + "=" * 56)
    print("  All examples complete!")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())
