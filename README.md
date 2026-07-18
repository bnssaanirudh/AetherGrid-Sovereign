# AetherGrid-Sovereign 🌐⚡

**Quantum-Fuzzy Heterogeneous Graph Transformer for Cascading Failure Prediction in Urban Digital Twins**

> *A Q1-Journal-Grade Soft Computing Framework for Smart City Disaster Resilience*

---

## Abstract

AetherGrid-Sovereign presents a novel hybrid soft computing architecture for predicting cascading infrastructure failures in Urban Digital Twins (UDTs) during disaster scenarios. The framework fuses a Heterogeneous Graph Transformer (HGT) with Intuitionistic Fuzzy Logic attention mechanisms and a Quantum-Inspired African Vulture Optimization Algorithm (Q-AVOA) for Neural Architecture Search. Unlike hard AI models that operate under closed-world assumptions, our Quantum-Fuzzy Attention ($A_{QF}$) explicitly models hesitation and non-deterministic entropy inherent in real-time disaster data streams, yielding superior cascading failure prediction under extreme uncertainty.

---

## Mathematical Framework

### Quantum-Fuzzy Attention

$$A_{QF} = \text{Norm}\left(\mu(e) \cdot e^{i\theta} + \nu(e)\right)$$

- $\mu(e) \in [0,1]$: Intuitionistic fuzzy **membership** (confidence that edge $e$ is active)
- $\nu(e) \in [0,1]$: Intuitionistic fuzzy **non-membership** (confidence that edge $e$ is failed)
- $\pi(e) = 1 - \mu(e) - \nu(e)$: **Hesitation margin** (irreducible uncertainty)
- $\theta$: Quantum phase-shift encoding temporal decay of sensor reliability

**Constraint:** $\mu(e) + \nu(e) \leq 1$ ensures valid IFS space.

---

## Architecture

```
Urban Sensor Streams → Graph Constructor → Sovereign Watchdog
                                                    ↓
                              Q-AVOA NAS ← HGT + IFS Attention
                                                    ↓
                              Cascading Failure Probability Map
```

---

## Project Structure

```
AetherGrid-Sovereign/
├── core/
│   ├── __init__.py
│   ├── graph_constructor.py        # Heterogeneous graph builder
│   ├── fuzzy_attention.py          # Intuitionistic Fuzzy Attention layer
│   ├── hgt_model.py                # Heterogeneous Graph Transformer
│   └── quantum_fuzzy_fusion.py     # QF-Attention mechanism
├── optimization/
│   ├── __init__.py
│   ├── q_avoa.py                   # Quantum-Inspired African Vulture Optimizer
│   ├── chaotic_maps.py             # Chaotic initialization maps
│   └── nas_search.py               # Neural Architecture Search wrapper
├── watchdog/
│   ├── __init__.py
│   └── sovereign_watchdog.py       # Pydantic-based graph integrity validator
├── data/
│   ├── __init__.py
│   ├── dataset_loaders.py          # OSM, WeatherBench, Urban-KG loaders
│   ├── preprocessing.py            # Normalization and fusion pipeline
│   ├── toy_dataset.py              # Toy graph loader
│   └── toy_graph.json              # Toy graph data
├── configs/
│   ├── default_config.yaml
│   ├── experiment.yaml
│   └── nas_search_space.yaml
├── experiments/
│   ├── train.py                    # Main training script
│   ├── run_nas.py                  # NAS-only runner
│   └── test_aethergrid.py          # Unit tests
├── notebooks/
│   └── demo.ipynb
├── docs/
│   └── architecture_diagram.md
├── ui/
│   └── streamlit_app.py            # Streamlit UI
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Datasets

| Dataset | Type | URL |
|---------|------|-----|
| OpenStreetMap | Road/Infrastructure Graph | https://www.openstreetmap.org |
| WeatherBench | Atmospheric Hazard Timeseries | https://github.com/pangeo-data/WeatherBench |
| Urban-KG / Yelp-Chicago | POI & Social Vulnerability | https://github.com/WenMellors/BIGSCity-SIGIR2021 |

---

## Installation

Python 3.10+ is required.

```bash
pip install -r requirements.txt
```

Or install the package in editable mode:

```bash
pip install -e .
```

---

## Quick Start

Run training from the CLI using the default config:

```bash
python -m experiments.train --config configs/default_config.yaml
```

Use the small offline config (toy graph) for a fast sanity check:

```bash
python -m experiments.train --config configs/experiment.yaml
```

## CLI

If installed with `pip install -e .`, the following entry points are available:

```bash
aethergrid-train --config configs/default_config.yaml
aethergrid-nas --config configs/default_config.yaml
```

Programmatic usage:

```python
from core.hgt_model import AetherHGT
from optimization.q_avoa import QuantumVultureOptimizer
from watchdog.sovereign_watchdog import SovereignWatchdog

# Initialize and search
optimizer = QuantumVultureOptimizer(population_size=20, max_iter=50)
best_arch = optimizer.search()

model = AetherHGT(**best_arch)
watchdog = SovereignWatchdog()

# Validate before each epoch
watchdog.validate(graph_data)
model.train(graph_data)
```

---

## Reproducibility

- Set `training.seed` in the config and pass `--seed` at runtime to control RNGs.
- Deterministic flags can be enabled for PyTorch (see `experiments/train.py`).
- Record environment info (Python, OS, CUDA) in your experiment logs for parity.

---

## UI (Streamlit)

```bash
streamlit run ui/streamlit_app.py
```

The UI runs on the fixed toy graph in data/toy_graph.json, so it works offline.

---

## Citation

```bibtex
@article{aethergrid2025,
  title={AetherGrid-Sovereign: Quantum-Fuzzy Heterogeneous Graph Transformers 
         for Cascading Failure Prediction in Urban Digital Twins},
  journal={Applied Soft Computing},
  year={2025}
}
```
