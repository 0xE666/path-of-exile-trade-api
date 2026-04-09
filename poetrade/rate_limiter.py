from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Mapping

@dataclass
class RateRule:
    """One rate limit rule: max_hits in window seconds, penalty on violation."""
    max_hits: int
    window: int
    penalty: int
    current: int = 0
    penalty_remaining: float = 0.0

@dataclass
class PolicyState:
    """All rules for a single rate limit policy."""
    rules: list[RateRule] = field(default_factory=list)

class RateLimiter:
    """Tracks rate limits per policy from API response headers."""

    def __init__(self):
        self._policies: dict[str, PolicyState] = {}

    def update(self, policy: str, headers: Mapping[str, str]) -> None:
        """Parse rate limit headers and update internal state."""
        rules_header = headers.get("X-Rate-Limit-Rules", "")
        if not rules_header:
            return
        rule_names = [r.strip() for r in rules_header.split(",")]
        all_rules: list[RateRule] = []
        for rule_name in rule_names:
            limit_header = headers.get(f"X-Rate-Limit-{rule_name}", "")
            state_header = headers.get(f"X-Rate-Limit-{rule_name}-State", "")
            if not limit_header:
                continue
            limits = limit_header.split(",")
            states = state_header.split(",") if state_header else []
            for i, limit_str in enumerate(limits):
                parts = limit_str.strip().split(":")
                if len(parts) != 3:
                    continue
                max_hits, window, penalty = int(parts[0]), int(parts[1]), int(parts[2])
                current = 0
                penalty_remaining = 0.0
                if i < len(states):
                    state_parts = states[i].strip().split(":")
                    if len(state_parts) == 3:
                        current = int(state_parts[0])
                        penalty_remaining = float(state_parts[2])
                all_rules.append(RateRule(max_hits=max_hits, window=window, penalty=penalty, current=current, penalty_remaining=penalty_remaining))
        self._policies[policy] = PolicyState(rules=all_rules)

    def get_state(self, policy: str) -> PolicyState | None:
        return self._policies.get(policy)

    def wait_time(self, policy: str) -> float:
        state = self._policies.get(policy)
        if state is None:
            return 0.0
        max_wait = 0.0
        for rule in state.rules:
            if rule.penalty_remaining > 0:
                max_wait = max(max_wait, rule.penalty_remaining)
            elif rule.current >= rule.max_hits - 1:
                max_wait = max(max_wait, float(rule.window))
        return max_wait

    async def acquire(self, policy: str) -> None:
        wait = self.wait_time(policy)
        if wait > 0:
            await asyncio.sleep(wait)

    def handle_429(self, headers: Mapping[str, str]) -> float:
        retry_after = headers.get("Retry-After", "60")
        try:
            return float(retry_after)
        except ValueError:
            return 60.0
