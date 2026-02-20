# SPDX-FileCopyrightText: 2026-present Demi <bjaiye1@gmail.com>
#
# SPDX-License-Identifier: MIT
"""State comparison monitor for multi-model spaces."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import biosim
from biosim.signals import BioSignal, SignalMetadata


class StateComparisonMonitor(biosim.BioModule):
    """Compare up to four incoming state streams.

    The monitor ingests `state_a..state_d`, computes scalar projections from
    heterogeneous dictionaries, and emits comparison summaries plus visuals.
    """

    def __init__(self, max_points: int = 2000, min_dt: float = 1.0) -> None:
        self.min_dt = float(min_dt)
        self.max_points = int(max_points)
        self._latest: Dict[str, Dict[str, Any]] = {}
        self._series: Dict[str, List[List[float]]] = {}
        self._last_t: float = 0.0
        self._outputs: Dict[str, BioSignal] = {}

    def inputs(self) -> Set[str]:
        return {"state_a", "state_b", "state_c", "state_d"}

    def outputs(self) -> Set[str]:
        return {"comparison_state"}

    def reset(self) -> None:
        self._latest = {}
        self._series = {}
        self._last_t = 0.0
        self._outputs = {}

    def _scalar_projection(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            nums: List[float] = []
            for v in value.values():
                if isinstance(v, (int, float)):
                    nums.append(float(v))
            if nums:
                return float(sum(nums) / len(nums))
        if isinstance(value, list):
            nums = [float(v) for v in value if isinstance(v, (int, float))]
            if nums:
                return float(sum(nums) / len(nums))
        return 0.0

    def set_inputs(self, signals: Dict[str, BioSignal]) -> None:
        for name in sorted(self.inputs()):
            sig = signals.get(name)
            if sig is None:
                continue
            t = float(sig.time)
            scalar = self._scalar_projection(sig.value)
            self._latest[name] = {
                "t": t,
                "scalar": scalar,
                "source": str(sig.source),
            }
            self._series.setdefault(name, []).append([t, scalar])
            if len(self._series[name]) > self.max_points:
                self._series[name] = self._series[name][-self.max_points :]
            self._last_t = max(self._last_t, t)

    def advance_to(self, t: float) -> None:
        now = float(max(t, self._last_t))
        active = [k for k in sorted(self._latest.keys()) if k in self.inputs()]
        latest_values = {k: float(self._latest[k]["scalar"]) for k in active}
        deltas: Dict[str, float] = {}
        for i, left in enumerate(active):
            for right in active[i + 1 :]:
                key = f"{left}_minus_{right}"
                deltas[key] = float(latest_values[left] - latest_values[right])

        source_name = getattr(self, "_world_name", self.__class__.__name__)
        self._outputs = {
            "comparison_state": BioSignal(
                source=source_name,
                name="comparison_state",
                value={
                    "t": now,
                    "latest_values": latest_values,
                    "pairwise_deltas": deltas,
                    "n_streams": len(active),
                },
                time=now,
                metadata=SignalMetadata(description="State comparison summary", kind="state"),
            )
        }

    def get_outputs(self) -> Dict[str, BioSignal]:
        return dict(self._outputs)

    def visualize(self) -> Optional[List[Dict[str, Any]]]:
        if not self._series:
            return None

        timeseries = {
            "render": "timeseries",
            "data": {
                "title": "State Stream Comparison",
                "series": [
                    {"name": name, "points": points}
                    for name, points in sorted(self._series.items())
                ],
            },
            "description": "Scalar projections for each incoming state stream.",
        }

        rows: List[List[str]] = []
        latest_values = {}
        if "comparison_state" in self._outputs:
            latest_values = self._outputs["comparison_state"].value.get("latest_values", {})
        for k in sorted(latest_values.keys()):
            rows.append([k, f"{float(latest_values[k]):.6f}"])

        table = {
            "render": "table",
            "data": {
                "columns": ["Stream", "Latest Scalar"],
                "rows": rows,
            },
            "description": "Latest scalar value per state input stream.",
        }

        return [timeseries, table]
