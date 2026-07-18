"""
chaotic_maps.py
---------------
Chaotic initialization maps for the Quantum-Inspired African Vulture
Optimization Algorithm. Chaos-based initialization improves population
diversity far beyond uniform random sampling.

Available maps:
  - Logistic map      (r=3.99, highly chaotic)
  - Tent map          (widely used in metaheuristics)
  - Sine map          (smooth ergodic chaos)
  - Chebyshev map     (uniform invariant distribution)
  - Gauss/Mouse map   (non-autonomous, aperiodic)
"""

from __future__ import annotations

import numpy as np
from typing import Literal

ChaoticMapType = Literal["logistic", "tent", "sine", "chebyshev", "gauss"]


def generate_chaotic_sequence(
    length: int,
    map_type: ChaoticMapType = "tent",
    x0: float = 0.7,
) -> np.ndarray:
    """
    Generate a 1-D chaotic sequence of given length.

    Parameters
    ----------
    length : int
    map_type : str
    x0 : float  Initial condition in (0, 1), avoid fixed points.

    Returns
    -------
    np.ndarray of shape (length,) with values in (0, 1).
    """
    x = float(x0)
    assert 0 < x < 1, "Initial condition must be strictly in (0, 1)"
    seq = np.empty(length, dtype=np.float64)

    if map_type == "logistic":
        r = 3.9999
        for i in range(length):
            x = r * x * (1.0 - x)
            seq[i] = x

    elif map_type == "tent":
        mu = 0.7  # slightly asymmetric for better ergodicity
        for i in range(length):
            x = x / mu if x < mu else (1.0 - x) / (1.0 - mu)
            seq[i] = x

    elif map_type == "sine":
        for i in range(length):
            x = np.sin(np.pi * x)
            seq[i] = x

    elif map_type == "chebyshev":
        # x_{n+1} = cos(k * arccos(x_n))  mapped to (0,1)
        k = 4
        for i in range(length):
            x = np.cos(k * np.arccos(np.clip(2.0 * x - 1.0, -1, 1)))
            x = (x + 1.0) / 2.0   # map (-1,1) -> (0,1)
            seq[i] = x

    elif map_type == "gauss":
        for i in range(length):
            x = np.exp(-x**2 / 0.1) + 0.89248  # Gauss/Mouse map
            x = x - np.floor(x)                  # keep in (0, 1)
            seq[i] = x

    else:
        raise ValueError(f"Unknown map_type: {map_type}")

    return seq


def chaotic_population_init(
    pop_size: int,
    dim: int,
    lb: np.ndarray,
    ub: np.ndarray,
    map_type: ChaoticMapType = "tent",
) -> np.ndarray:
    """
    Initialise a population using a chaotic map.

    Parameters
    ----------
    pop_size : int   Number of individuals.
    dim : int        Decision variable dimensionality.
    lb, ub : arrays  Lower/upper bounds [dim].
    map_type : str

    Returns
    -------
    population : np.ndarray [pop_size, dim]
    """
    population = np.empty((pop_size, dim), dtype=np.float64)
    for d in range(dim):
        x0 = 0.1 + 0.8 * np.random.random()   # random x0 per dimension
        seq = generate_chaotic_sequence(pop_size, map_type=map_type, x0=x0)
        population[:, d] = lb[d] + seq * (ub[d] - lb[d])
    return population
