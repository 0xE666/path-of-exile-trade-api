"""PoB build pricer — fetch a pobb.in link, extract items, search trade API for each."""
from __future__ import annotations

import base64
import re
import zlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

from .client import TradeClient
from .query_builder import QueryBuilder
from .models.search import SearchResponse, StatFilter
from .models.fetch import FetchResult
from .models.common import Range


@dataclass
class PoBItem:
    """Parsed item from a PoB XML."""
    slot: str
    item_id: str
    rarity: str  # UNIQUE, RARE, MAGIC, RELIC
    name: str
    base_type: str
    implicits: list[str] = field(default_factory=list)
    explicits: list[str] = field(default_factory=list)
    fractured: list[str] = field(default_factory=list)
    crafted: list[str] = field(default_factory=list)
    corrupted: bool = False
    ilvl: int = 0
    quality: int = 0
    ward: int = 0
    armour: int = 0
    evasion: int = 0
    es: int = 0
    is_fractured: bool = False
    is_split: bool = False
    is_foulborn: bool = False
    raw_text: str = ""


@dataclass
class PriceResult:
    """Trade search result for a PoB item."""
    item: PoBItem
    search_response: SearchResponse | None
    trade_url: str
    cheapest: list[FetchResult]
    error: str | None = None
    tier_label: str = ""  # Which tier found results (e.g. "T1 (90% rolls)")


def fetch_pob_code(pobb_url: str) -> str:
    """Fetch raw PoB code from a pobb.in URL."""
    # Extract paste ID from URL
    paste_id = pobb_url.rstrip("/").split("/")[-1]
    url = f"https://pobb.in/pob/{paste_id}"
    req = Request(url, headers={"User-Agent": "poetrade-python/1.0"})
    with urlopen(req) as resp:
        return resp.read().decode("utf-8")


def decode_pob_xml(pob_code: str) -> ET.Element:
    """Decode a PoB import code to XML Element."""
    b64 = pob_code.replace("-", "+").replace("_", "/")
    if len(b64) % 4:
        b64 += "=" * (4 - len(b64) % 4)
    xml_bytes = zlib.decompress(base64.b64decode(b64))
    return ET.fromstring(xml_bytes)


def parse_item_text(text: str) -> PoBItem:
    """Parse a PoB item text block into a PoBItem."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines) < 3:
        return PoBItem(slot="", item_id="", rarity="UNKNOWN", name="", base_type="", raw_text=text)

    rarity = lines[0].replace("Rarity: ", "")
    name = lines[1]
    base_type = lines[2]

    # Parse the rest
    implicits = []
    explicits = []
    fractured = []
    crafted = []
    corrupted = False
    ilvl = 0
    quality = 0
    ward = 0
    armour = 0
    evasion = 0
    es = 0
    is_fractured = False
    is_split = False
    is_foulborn = "Foulborn" in name

    # Find where implicits/explicits start
    implicit_count = 0
    in_mods = False
    mod_line_idx = 0

    for line in lines[3:]:
        if line.startswith("Unique ID:") or line.startswith("WardBasePercentile") or line.startswith("ArmourBasePercentile") or line.startswith("EvasionBasePercentile") or line.startswith("EnergyShieldBasePercentile"):
            continue
        if line.startswith("Item Level:"):
            ilvl = int(line.split(":")[1].strip())
        elif line.startswith("Quality:"):
            quality = int(line.split(":")[1].strip())
        elif line.startswith("Ward:"):
            try:
                ward = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Armour:"):
            try:
                armour = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Evasion:"):
            try:
                evasion = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Energy Shield:"):
            try:
                es = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Implicits:"):
            implicit_count = int(line.split(":")[1].strip())
            in_mods = True
            mod_line_idx = 0
        elif line == "Corrupted":
            corrupted = True
        elif line == "Fractured Item":
            is_fractured = True
        elif line == "Split":
            is_split = True
        elif line.startswith("Sockets:") or line.startswith("LevelReq:") or line.startswith("Radius:"):
            continue
        elif line.startswith("Searing Exarch") or line.startswith("Eater of Worlds") or line.startswith("Crusader") or line.startswith("Redeemer") or line.startswith("Hunter") or line.startswith("Warlord") or line.startswith("Shaper") or line.startswith("Elder"):
            if "Item" in line:
                continue
        elif line.startswith("Foil Unique"):
            continue
        elif in_mods:
            # Check for {tags}
            is_crafted = line.startswith("{crafted}")
            is_frac = line.startswith("{fractured}")
            is_mutated = line.startswith("{mutated}")
            clean = re.sub(r"\{[^}]+\}", "", line).strip()

            if not clean:
                continue

            if mod_line_idx < implicit_count:
                implicits.append(clean)
            elif is_frac:
                fractured.append(clean)
            elif is_crafted:
                crafted.append(clean)
            else:
                explicits.append(clean)

            mod_line_idx += 1

    return PoBItem(
        slot="",
        item_id="",
        rarity=rarity,
        name=name,
        base_type=base_type,
        implicits=implicits,
        explicits=explicits,
        fractured=fractured,
        crafted=crafted,
        corrupted=corrupted,
        ilvl=ilvl,
        quality=quality,
        ward=ward,
        armour=armour,
        evasion=evasion,
        es=es,
        is_fractured=is_fractured,
        is_split=is_split,
        is_foulborn=is_foulborn,
        raw_text=text,
    )


def extract_items(root: ET.Element) -> list[PoBItem]:
    """Extract all equipped items from PoB XML."""
    items_section = root.find(".//Items")
    if items_section is None:
        return []

    # Build item_id -> PoBItem map
    item_map: dict[str, PoBItem] = {}
    for item_el in items_section.findall("Item"):
        item_id = item_el.get("id", "")
        text = item_el.text or ""
        if not text.strip():
            continue
        pob_item = parse_item_text(text)
        pob_item.item_id = item_id
        item_map[item_id] = pob_item

    # Build slot -> item_id map
    # Slots can be directly under Items OR inside ItemSet elements
    slot_map: dict[str, str] = {}
    for slot_el in items_section.findall("Slot"):
        slot_name = slot_el.get("name", "")
        item_id = slot_el.get("itemId", "0")
        if item_id != "0" and slot_name:
            slot_map[slot_name] = item_id
    # Also check inside ItemSet (active gear set)
    for item_set in items_section.findall("ItemSet"):
        for slot_el in item_set.findall("Slot"):
            slot_name = slot_el.get("name", "")
            item_id = slot_el.get("itemId", "0")
            if item_id != "0" and slot_name:
                slot_map[slot_name] = item_id

    # Assign slots and filter to equipped gear only
    equipped: list[PoBItem] = []
    # Superset of PoE 1 and PoE 2 (PoB2) slot names. PoE 2 adds a third ring
    # and charm slots; PoE 1 has up to five flasks. Slots absent from a given
    # build's XML simply don't match, so a superset is safe for both games.
    gear_slots = [
        "Helmet", "Body Armour", "Gloves", "Boots",
        "Weapon 1", "Weapon 2",
        "Ring 1", "Ring 2", "Ring 3",          # PoE 2 has 3 rings
        "Amulet", "Belt",
        "Charm 1", "Charm 2", "Charm 3",       # PoE 2 charms
        "Flask 1", "Flask 2", "Flask 3", "Flask 4", "Flask 5",
    ]

    for slot_name in gear_slots:
        item_id = slot_map.get(slot_name)
        if item_id and item_id in item_map:
            item = item_map[item_id]
            item.slot = slot_name
            equipped.append(item)

    # Also get abyssal socket jewels from slot map
    for slot_name, item_id in slot_map.items():
        if "Socket" in slot_name and item_id in item_map:
            item = item_map[item_id]
            item.slot = slot_name
            equipped.append(item)

    # Get tree jewel sockets from Spec/Socket elements
    for spec in root.iter("Spec"):
        for socket in spec.findall("Socket"):
            item_id = socket.get("itemId", "0")
            node_id = socket.get("nodeId", "")
            if item_id != "0" and item_id in item_map:
                item = item_map[item_id]
                if not item.slot:  # Don't double-add
                    item.slot = f"Tree Socket ({node_id})"
                    equipped.append(item)

    return equipped


async def build_query(
    item: PoBItem,
    client: TradeClient,
    tier_pct: float = 0.9,
) -> QueryBuilder | None:
    """Build a trade search query for a PoB item.

    Args:
        tier_pct: Fraction of original roll values to use as minimum (1.0 = exact, 0.5 = half)
    """
    q = QueryBuilder().sort("price", "asc")

    # Skip magic flasks
    if "Flask" in item.slot and item.rarity == "MAGIC":
        return None

    if item.rarity in ("UNIQUE", "RELIC"):
        clean_name = item.name
        if item.is_foulborn:
            clean_name = re.sub(r"^Foulborn\s+", "", clean_name)
        q = q.name(clean_name).filter("type_filters", rarity="unique")
        if item.is_foulborn:
            q = q.filter("misc_filters", mutated=True)
    elif item.rarity == "RARE":
        q = q.type(item.base_type).filter("type_filters", rarity="rare")

        all_mods = item.explicits + item.fractured
        stats = await _mods_to_stat_filters(all_mods, client, tier_pct=tier_pct)
        for stat in stats:
            q = q.stat(stat.id, min=stat.value.min if stat.value else None)

        # fractured_item filter is handled by the caller (tiered fallback)
    elif item.rarity == "MAGIC":
        return None
    else:
        return None

    return q


# Tier fallback percentages: T1 (90%), T2 (75%), T3 (60%), T4 (45%), Budget (30%)
TIER_FALLBACKS = [
    (0.90, "T1 (90% rolls)"),
    (0.75, "T2 (75% rolls)"),
    (0.60, "T3 (60% rolls)"),
    (0.45, "T4 (45% rolls)"),
    (0.30, "Budget (30% rolls)"),
]


async def _mods_to_stat_filters(mods: list[str], client: TradeClient, tier_pct: float = 0.9) -> list[StatFilter]:
    """Convert PoB mod text to trade API stat filters by searching the stats database."""
    stats_db = await client.get_stats()

    # Build lookup: normalized trade API text -> (stat_id, category)
    # Prefer explicit > fractured > crafted > implicit > pseudo for matching
    PRIORITY = {"explicit": 0, "fractured": 1, "implicit": 2, "crafted": 3,
                "enchant": 4, "pseudo": 5, "imbued": 6}
    stat_lookup: dict[str, list[tuple[str, str, int]]] = {}
    for category in stats_db:
        prio = PRIORITY.get(category.id, 10)
        for entry in category.entries:
            key = entry.text.strip().lower()
            if key not in stat_lookup:
                stat_lookup[key] = []
            stat_lookup[key].append((entry.id, category.id, prio))

    def find_stat(mod_text: str) -> tuple[str, float | None] | None:
        """Try to match a PoB mod string to a trade stat ID."""
        numbers = re.findall(r"[+-]?(\d+(?:\.\d+)?)", mod_text)
        value = float(numbers[0]) if numbers else None

        # Normalize: replace numbers with #, keep % signs in place
        # PoB: "+405 to Armour" -> trade: "+# to Armour"
        # PoB: "143% increased Armour" -> trade: "#% increased Armour"
        normalized = re.sub(r"[+-]?\d+(?:\.\d+)?", "#", mod_text).strip().lower()

        # Try exact match
        candidates = stat_lookup.get(normalized, [])

        # Try with + prefix added: "# to Armour" -> "+# to Armour"
        if not candidates:
            with_plus = re.sub(r"^#", "+#", normalized)
            candidates = stat_lookup.get(with_plus, [])

        # Try removing "(local)" suffix or adding it
        if not candidates:
            candidates = stat_lookup.get(normalized + " (local)", [])
        if not candidates:
            candidates = stat_lookup.get(normalized.replace(" (local)", ""), [])

        if candidates:
            # Pick highest priority (lowest number)
            best = min(candidates, key=lambda x: x[2])
            return (best[0], value)

        return None

    filters = []
    for mod in mods:
        result = find_stat(mod)
        if result and result[1] is not None:
            stat_id, val = result
            # Scale value by tier percentage
            min_val = round(val * tier_pct)
            if min_val > 0:
                filters.append(StatFilter(id=stat_id, value=Range(min=min_val)))

    return filters


async def price_build(
    pobb_url: str,
    client: TradeClient,
    league: str = "Standard",
    fetch_count: int = 3,
) -> list[PriceResult]:
    """Price all items from a PoB link with tiered fallback.

    For rare items, starts at T1 (90% of roll values). If 0 results,
    falls back to T2 (75%), T3 (60%), T4 (45%), Budget (30%) until
    listings are found.

    Args:
        pobb_url: pobb.in URL
        client: Authenticated TradeClient
        league: League to search in
        fetch_count: Number of results to fetch per item

    Returns:
        List of PriceResult for each equipped item
    """
    pob_code = fetch_pob_code(pobb_url)
    root = decode_pob_xml(pob_code)
    items = extract_items(root)

    results: list[PriceResult] = []

    for item in items:
        try:
            # Non-rares don't need tiered fallback
            if item.rarity not in ("RARE",):
                builder = await build_query(item, client)
                if builder is None:
                    results.append(PriceResult(
                        item=item, search_response=None, trade_url="",
                        cheapest=[], error="Skipped (unsupported item type)",
                    ))
                    continue

                query = builder.build()
                search_result = await client.search(league, query)
                trade_url = client.trade_url(search_result)
                cheapest = []
                if search_result.result:
                    cheapest = await client.fetch(search_result, limit=fetch_count)
                results.append(PriceResult(
                    item=item, search_response=search_result,
                    trade_url=trade_url, cheapest=cheapest,
                    tier_label="Unique" if item.rarity in ("UNIQUE", "RELIC") else "",
                ))
                continue

            # Rare items: tiered fallback
            found = False
            last_search = None
            last_url = ""
            for tier_pct, tier_label in TIER_FALLBACKS:
                builder = await build_query(item, client, tier_pct=tier_pct)
                if builder is None:
                    break

                # Relax fractured requirement at lower tiers
                if item.is_fractured and tier_pct < 0.75:
                    pass  # Don't add fractured filter at T3+
                elif item.is_fractured:
                    builder = builder.filter("misc_filters", fractured_item=True)

                query = builder.build()
                search_result = await client.search(league, query)
                trade_url = client.trade_url(search_result)
                last_search = search_result
                last_url = trade_url

                if search_result.total > 0:
                    cheapest = await client.fetch(search_result, limit=fetch_count)
                    results.append(PriceResult(
                        item=item, search_response=search_result,
                        trade_url=trade_url, cheapest=cheapest,
                        tier_label=tier_label,
                    ))
                    found = True
                    break

            if not found:
                results.append(PriceResult(
                    item=item, search_response=last_search,
                    trade_url=last_url, cheapest=[],
                    tier_label="No matches at any tier",
                ))

        except Exception as e:
            results.append(PriceResult(
                item=item, search_response=None, trade_url="",
                cheapest=[], error=str(e),
            ))

    return results
