# models-observability

Public curated monitor model repository for Biosimulant spaces.

This repo provides reusable observability models that can be referenced from spaces in other split repos.

## Included Models

- `observability-state-comparison-monitor`
  - Inputs: `state_a`, `state_b`, `state_c`, `state_d`
  - Outputs: `comparison_state`
  - Visuals: `timeseries` + `table`

- `observability-state-metrics-monitor`
  - Inputs: `state_a`, `state_b`, `state_c`, `state_d`
  - Outputs: `metrics`
  - Visuals: `timeseries` + `table`

## Validation

```bash
python scripts/validate_manifests.py
python scripts/check_entrypoints.py
```
