"""Access policy: which metrics (by sensitivity) and which rows (by region) a role may see."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

POLICY_PATH = Path(__file__).resolve().parents[3] / "policies" / "access_policy.yml"


@dataclass
class Decision:
    allowed: bool
    reason: str = ""
    forced_filters: dict | None = None   # row-level filters the policy adds, whatever the plan said
    restricted: bool = False


class AccessPolicy:
    def __init__(self, spec: dict):
        self.spec = spec
        self.roles: dict = spec["roles"]
        self.order: list = spec["sensitivity_order"]
        self.scope_dim: str = spec["row_scope_dimension"]
        self.max_rows: int = spec["limits"]["max_result_rows"]

    @classmethod
    def load(cls, path: Path | str = POLICY_PATH) -> "AccessPolicy":
        with open(path) as f:
            return cls(yaml.safe_load(f))

    def check(self, role: str, metric_sensitivity: dict[str, str], filters: dict[str, list]) -> Decision:
        if role not in self.roles:
            return Decision(False, f"unknown role {role!r} - access is denied by default")
        r = self.roles[role]
        limit = self.order.index(r["max_sensitivity"])
        too_sensitive = [m for m, s in metric_sensitivity.items() if self.order.index(s) > limit]
        if too_sensitive:
            levels = sorted({metric_sensitivity[m] for m in too_sensitive})
            return Decision(False, f"{', '.join(too_sensitive)} is classified {', '.join(levels)}; "
                                   f"role {role} may see up to {r['max_sensitivity']}")
        if r["regions"] == ["*"]:
            return Decision(True)
        allowed = set(r["regions"])
        asked = set(filters.get(self.scope_dim, []))
        if asked and not asked <= allowed:
            return Decision(False, f"role {role} may only see region(s) {sorted(allowed)}; "
                                   f"the question asks for {sorted(asked - allowed)}")
        return Decision(True, forced_filters={self.scope_dim: sorted(asked or allowed)},
                        restricted=not asked,
                        reason=f"results limited to region(s) {sorted(asked or allowed)} for role {role}")
