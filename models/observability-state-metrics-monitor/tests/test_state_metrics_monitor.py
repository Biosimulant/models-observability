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
    module_path = MODEL_ROOT / "src" / "state_metrics_monitor.py"
    spec = importlib.util.spec_from_file_location("observability_state_metrics_monitor", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.StateMetricsMonitor


StateMetricsMonitor = _load_monitor_cls()


def _sig(source: str, name: str, value: object, t: float) -> BioSignal:
    return BioSignal(source=source, name=name, value=value, time=t, metadata=SignalMetadata(kind="state"))


def test_metrics_monitor_contracts() -> None:
    mon = StateMetricsMonitor()
    assert mon.inputs() == {"state_a", "state_b", "state_c", "state_d"}
    assert mon.outputs() == {"metrics"}


def test_metrics_monitor_outputs_and_visuals() -> None:
    mon = StateMetricsMonitor(max_points=10, min_dt=1.0)
    mon.set_inputs(
        {
            "state_a": _sig("a", "state_a", {"x": 1.0, "y": 3.0}, 1.0),
            "state_b": _sig("b", "state_b", 5.0, 1.0),
        }
    )
    mon.set_inputs({"state_a": _sig("a", "state_a", {"x": 3.0, "y": 5.0}, 2.0)})
    mon.advance_to(2.0)

    out = mon.get_outputs()
    assert "metrics" in out
    payload = out["metrics"].value
    assert payload["stream_count"] >= 1
    assert "state_a" in payload["stream_metrics"]

    vis = mon.visualize()
    assert vis is not None
    renders = {v["render"] for v in vis}
    assert "timeseries" in renders
    assert "table" in renders
