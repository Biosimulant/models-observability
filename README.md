# models-observability

Curated **observability** monitor models for the **biosim** platform. This repository provides reusable monitoring and comparison tools that can be referenced from spaces across all model repositories.

## What's Inside

### Models (2 packages)

**Observability** — state monitoring, comparison, and metrics calculation:

- `observability-state-comparison-monitor` — Compares multiple state inputs with timeseries and table visualizations
- `observability-state-metrics-monitor` — Calculates metrics from state inputs with timeseries and table output

These models are designed to be cross-cutting utilities for monitoring and analyzing simulation states across different biological domains.

## Prerequisites
```bash
pip install "biosim @ git+https://github.com/BioSimulant/biosim.git@main"
```

## License
Dual-licensed: Apache-2.0 (code), CC BY 4.0 (content)
