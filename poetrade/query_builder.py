from __future__ import annotations
from .models.common import Range, StatusOption, SortOption
from .models.search import StatFilter, StatGroup, Filters, SearchQuery, SearchRequest

class QueryBuilder:
    def __init__(self):
        self._name: str | dict | None = None
        self._type: str | dict | None = None
        self._term: str | None = None
        self._status: str = "any"
        self._stat_filters: list[StatFilter] = []
        self._stat_groups: list[StatGroup] = []
        self._filters: dict[str, dict] = {}
        self._sort_key: str | None = "price"
        self._sort_dir: str = "asc"

    def name(self, name: str | dict) -> QueryBuilder:
        self._name = name
        return self

    def type(self, type_: str | dict) -> QueryBuilder:
        self._type = type_
        return self

    def term(self, term: str) -> QueryBuilder:
        self._term = term
        return self

    def status(self, option: str) -> QueryBuilder:
        self._status = option
        return self

    def stat(self, stat_id: str, *, min: float | None = None, max: float | None = None) -> QueryBuilder:
        value = Range(min=min, max=max) if min is not None or max is not None else None
        self._stat_filters.append(StatFilter(id=stat_id, value=value))
        return self

    def stat_group(self, group_type: str, *, filters: list[StatFilter], min_match: int | None = None, min_weight: float | None = None) -> QueryBuilder:
        value = None
        if min_match is not None:
            value = Range(min=min_match)
        elif min_weight is not None:
            value = Range(min=min_weight)
        self._stat_groups.append(StatGroup(type=group_type, filters=filters, value=value))
        return self

    def filter(self, group: str, **kwargs) -> QueryBuilder:
        if group not in self._filters:
            self._filters[group] = {}
        inner = self._filters[group]
        processed: dict[str, dict] = {}
        for key, val in kwargs.items():
            if key.startswith("price_"):
                suffix = key[6:]
                if "price" not in processed:
                    processed["price"] = inner.get("price", {})
                if suffix == "currency":
                    processed["price"]["option"] = val
                else:
                    processed["price"][suffix] = val
                continue
            for range_suffix in ("_min", "_max"):
                if key.endswith(range_suffix):
                    field = key[: -len(range_suffix)]
                    range_key = range_suffix[1:]
                    if field not in processed:
                        processed[field] = inner.get(field, {})
                    processed[field][range_key] = val
                    break
            else:
                if isinstance(val, bool):
                    processed[key] = {"option": str(val).lower()}
                else:
                    processed[key] = {"option": val}
        inner.update(processed)
        return self

    def sort(self, key: str, direction: str = "asc") -> QueryBuilder:
        self._sort_key = key
        self._sort_dir = direction
        return self

    def build(self) -> SearchRequest:
        stats: list[StatGroup] = []
        if self._stat_filters:
            stats.append(StatGroup(type="and", filters=self._stat_filters))
        stats.extend(self._stat_groups)
        filters_dict = {}
        for group_name, group_filters in self._filters.items():
            filters_dict[group_name] = {"filters": group_filters}
        filters = Filters(**filters_dict)
        query = SearchQuery(status=StatusOption(option=self._status), name=self._name, type=self._type, term=self._term, stats=stats, filters=filters)
        sort = SortOption()
        if self._sort_key == "price":
            sort = SortOption(price=self._sort_dir)
        elif self._sort_key == "have":
            sort = SortOption(have=self._sort_dir)
        return SearchRequest(query=query, sort=sort)
