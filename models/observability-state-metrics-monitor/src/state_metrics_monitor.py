# SPDX-FileCopyrightText: 2026-present Demi <bjaiye1@gmail.com>
#
# SPDX-License-Identifier: MIT
"""State metrics monitor for multi-model spaces."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import biosim
from biosim.signals import BioSignal, SignalMetadata


class StateMetricsMonitor(biosim.BioModule):
    """Compute simple descriptive metrics over up to four state streams."""

    def __init__(self, max_points: int = 2000, min_dt: float = 1.0) -> None:
        self.min_dt = float(min_dt)
        self.max_points = int(max_points)
        self._history: Dict[str, List[float]] = {}
        self._latest_t: float = 0.0
        self._outputs: Dict[str, BioSignal] = {}

    def inputs(self) -> Set[str]:
        return {"state_a", "state_b", "state_c", "state_d"}

    def outputs(self) -> Set[str]:
        return {"metrics"}

    def reset(self) -> None:
        self._history = {}
        self._latest_t = 0.0
        self._outputs = {}

    def _extract_scalar(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            nums = [float(v) for v in value.values() if isinstance(v, (int, float))]
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
            scalar = self._extract_scalar(sig.value)
            self._history.setdefault(name, []).append(scalar)
            if len(self._history[name]) > self.max_points:
                self._history[name] = self._history[name][-self.max_points :]
            self._latest_t = max(self._latest_t, float(sig.time))

    def _summary(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
        count = float(len(values))
        return {
            "count": count,
            "mean": float(sum(values) / len(values)),
            "min": float(min(values)),
            "max": float(max(values)),
        }

    def advance_to(self, t: float) -> None:
        now = float(max(t, self._latest_t))
        per_stream = {k: self._summary(v) for k, v in sorted(self._history.items())}

        source_name = getattr(self, "_world_name", self.__class__.__name__)
        self._outputs = {
            "metrics": BioSignal(
                source=source_name,
                name="metrics",
                value={
                    "t": now,
                    "stream_metrics": per_stream,
                    "stream_count": len(per_stream),
                },
                time=now,
                metadata=SignalMetadata(description="State stream metrics summary", kind="state"),
            )
        }

    def get_outputs(self) -> Dict[str, BioSignal]:
        return dict(self._outputs)

    def visualize(self) -> Optional[List[Dict[str, Any]]]:
        if not self._history:
            return None

        series = []
        for name, vals in sorted(self._history.items()):
            points = [[float(i), float(v)] for i, v in enumerate(vals)]
            series.append({"name": name, "points": points})

        rows: List[List[str]] = []
        metrics = {}
        if "metrics" in self._outputs:
            metrics = self._outputs["metrics"].value.get("stream_metrics", {})
        for name in sorted(metrics.keys()):
            m = metrics[name]
            rows.append([
                name,
                str(int(m["count"])),
                f"{float(m['mean']):.6f}",
                f"{float(m['min']):.6f}",
                f"{float(m['max']):.6f}",
            ])

        return [
            {
                "render": "timeseries",
                "data": {
                    "title": "State Stream Metrics (Scalar History)",
                    "series": series,
                },
                "description": "Scalar history per stream for quick trend checks.",
            },
            {
                "render": "table",
                "data": {
                    "columns": ["Stream", "Count", "Mean", "Min", "Max"],
                    "rows": rows,
                },
                "description": "Descriptive metrics for each stream.",
            },
        ]
