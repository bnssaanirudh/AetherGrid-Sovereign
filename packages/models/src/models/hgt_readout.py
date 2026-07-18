"""Readout heads for AetherHGT."""

from __future__ import annotations

import torch.nn as nn


def make_failure_readout(hidden_dim: int, dropout: float) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(hidden_dim, hidden_dim // 2),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(hidden_dim // 2, 1),
        nn.Sigmoid(),
    )
