"""
test_simulator.py
-----------------
Verifies the CascadeSimulator on small oracle graphs and checks monotonicity rules.
"""

from __future__ import annotations

import pytest
from evaluation import CascadeSimulator


def test_tiny_graph_oracle():
    # Tiny linear graph: A -> B -> C
    node_positions = {
        "A": (0.0, 0.0),
        "B": (1.0, 0.0),
        "C": (2.0, 0.0),
    }
    adjacency = {
        "A": ["B"],
        "B": ["C"],
        "C": [],
    }

    # If propagation probability is 1.0, everything should fail if A fails
    sim = CascadeSimulator(
        seed=101,
        hazard_intensity=0.8,
        propagation_probability=1.0,
        vulnerability_threshold=0.5
    )
    
    failures, manifest = sim.run(node_positions, adjacency, trigger_node="A")
    assert failures["A"] is True
    assert failures["B"] is True
    assert failures["C"] is True
    assert manifest.cascade_size == 3
    assert manifest.graph_radius_hops == 2


def test_cascade_monotonicity():
    node_positions = {f"n_{i}": (float(i), 0.0) for i in range(10)}
    adjacency = {f"n_{i}": [f"n_{i+1}"] for i in range(9)}
    adjacency["n_9"] = []

    # Verify that as hazard intensity increases, cascade size is monotonic (non-decreasing)
    cascade_sizes = []
    intensities = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    for h in intensities:
        sim = CascadeSimulator(
            seed=42,
            hazard_intensity=h,
            propagation_probability=0.5,
            vulnerability_threshold=0.4
        )
        _, manifest = sim.run(node_positions, adjacency, trigger_node="n_0")
        cascade_sizes.append(manifest.cascade_size)

    # Assert non-decreasing sequence
    for i in range(1, len(cascade_sizes)):
        assert cascade_sizes[i] >= cascade_sizes[i - 1], f"Monotonicity violated: {cascade_sizes}"
