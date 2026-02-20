from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]

for p in [MODEL_ROOT, *MODEL_ROOT.parents]:
    bsim_src = p / "bsim" / "src"
    if bsim_src.exists() and str(bsim_src) not in sys.path:
        sys.path.insert(0, str(bsim_src))
        break
    biosim_src = p / "biosim" / "src"
    if biosim_src.exists() and str(biosim_src) not in sys.path:
        sys.path.insert(0, str(biosim_src))
        break

from biosim.signals import BioSignal, SignalMetadata


def _load_monitor_cls():
    module_path = MODEL_ROOT / "src" / "state_comparison_monitor.py"
    spec = importlib.util.spec_from_file_location("observability_state_comparison_monitor", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.StateComparisonMonitor


StateComparisonMonitor = _load_monitor_cls()


def _sig(source: str, name: str, value: object, t: float) -> BioSignal:
    return BioSignal(source=source, name=name, value=value, time=t, metadata=SignalMetadata(kind="state"))


def test_monitor_contracts() -> None:
    mon = StateComparisonMonitor()
    assert mon.inputs() == {"state_a", "state_b", "state_c", "state_d"}
    assert mon.outputs() == {"comparison_state"}


def test_monitor_outputs_and_visuals() -> None:
    mon = StateComparisonMonitor(max_points=10, min_dt=1.0)
    mon.set_inputs(
        {
            "state_a": _sig("a", "state_a", {"x": 10.0, "y": 20.0}, 1.0),
            "state_b": _sig("b", "state_b", {"x": 4.0, "z": 8.0}, 1.0),
        }
    )
    mon.advance_to(1.0)
    outputs = mon.get_outputs()
    assert "comparison_state" in outputs
    payload = outputs["comparison_state"].value
    assert payload["n_streams"] == 2
    assert "state_a_minus_state_b" in payload["pairwise_deltas"]

    vis = mon.visualize()
    assert vis is not None
    assert isinstance(vis, list)
    renders = {v["render"] for v in vis}
    assert "timeseries" in renders
    assert "table" in renders
