"""
preprocessing.py
----------------
Normalization, temporal alignment, and feature fusion for multi-modal
urban datasets before injection into the heterogeneous graph.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import torch


def z_score_normalize(features: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Z-score normalization per feature column."""
    if features.ndim != 2:
        raise ValueError("features must be 2D [N, D]")
    features = features.astype(np.float32, copy=False)
    mean = features.mean(axis=0, keepdims=True)
    std  = features.std(axis=0, keepdims=True)
    return (features - mean) / (std + eps)


def min_max_normalize(features: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Min-max normalization to [0, 1]."""
    if features.ndim != 2:
        raise ValueError("features must be 2D [N, D]")
    features = features.astype(np.float32, copy=False)
    mn = features.min(axis=0, keepdims=True)
    mx = features.max(axis=0, keepdims=True)
    return (features - mn) / (mx - mn + eps)


def fuse_temporal_weather(
    base_features: np.ndarray,    # [N, D]
    weather_snapshot: np.ndarray, # [N_grid, 4]  (one timestep)
    strategy: str = "concat_reduced",
) -> np.ndarray:
    """
    Fuse static node features with a weather snapshot.

    strategy = 'concat_reduced': PCA-reduces weather to 2 dims, then concat.
    """
    if base_features.ndim != 2:
        raise ValueError("base_features must be 2D [N, D]")
    if weather_snapshot.ndim != 2:
        raise ValueError("weather_snapshot must be 2D [N_grid, 4]")

    base_features = base_features.astype(np.float32, copy=False)
    weather_snapshot = weather_snapshot.astype(np.float32, copy=False)

    n = len(base_features)
    # Repeat or subsample weather to match node count
    if len(weather_snapshot) >= n:
        weather = weather_snapshot[:n]
    else:
        idx = np.random.choice(len(weather_snapshot), n, replace=True)
        weather = weather_snapshot[idx]

    if strategy == "concat_reduced":
        # Simple dimensionality reduction: take first 2 PCs via SVD
        w_norm = min_max_normalize(weather)
        if w_norm.shape[1] > 2:
            U, S, Vt = np.linalg.svd(w_norm, full_matrices=False)
            w_reduced = (w_norm @ Vt[:2].T)   # [N, 2]
        else:
            w_reduced = w_norm
        return np.concatenate([base_features, w_reduced], axis=1).astype(np.float32)

    return base_features


def build_ifs_edge_attributes(
    edge_index: torch.Tensor,
    base_weight: torch.Tensor,
    damage_proxy: torch.Tensor,
    temporal_decay: torch.Tensor,
) -> torch.Tensor:
    """
    Construct IFS-compliant edge attributes [mu, nu, weight, tau].

    mu  = 1 - damage_proxy       (higher damage → lower membership)
    nu  = damage_proxy * (1 - temporal_decay)
    Constraint: mu + nu = 1 - damage_proxy*(1 - (1-damage_proxy)*temporal_decay) ≤ 1
    """
    if base_weight.ndim != 1 or damage_proxy.ndim != 1 or temporal_decay.ndim != 1:
        raise ValueError("base_weight, damage_proxy, temporal_decay must be 1D tensors")
    if not (base_weight.size(0) == damage_proxy.size(0) == temporal_decay.size(0)):
        raise ValueError("base_weight, damage_proxy, temporal_decay must have same length")

    mu  = 1.0 - damage_proxy
    nu  = damage_proxy * (1.0 - temporal_decay)
    # Ensure IFS constraint
    excess = torch.clamp(mu + nu - 1.0, min=0.0)
    nu = nu - excess / 2.0
    mu = mu - excess / 2.0
    return torch.stack([mu, nu, base_weight, temporal_decay], dim=1)
