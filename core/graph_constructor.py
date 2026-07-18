"""
graph_constructor.py
--------------------
Builds a PyTorch Geometric HeteroData graph from multi-modal urban layers:
  - Power Stations  (node type: 'power')
  - Hospitals       (node type: 'hospital')
  - Road Segments   (node type: 'road')
  - Citizens/Zones  (node type: 'citizen')

Edge types capture physical/logical dependencies between layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from torch_geometric.data import HeteroData

from .schema import EDGE_TYPES, FEATURE_DIMS, NODE_TYPES

logger = logging.getLogger(__name__)


@dataclass
class GraphConfig:
    num_power:    int = 50
    num_hospital: int = 20
    num_road:     int = 200
    num_citizen:  int = 100
    edge_density: float = 0.05    # sparse: ~5% of max possible edges
    add_self_loops: bool = False
    normalize_features: bool = True
    seed: int = 42
    use_toy_data: bool = False
    toy_data_path: Optional[str] = None


class UrbanGraphConstructor:
    """
    Constructs and manages the heterogeneous urban infrastructure graph.

    In production, replace the synthetic generators with loaders from
    data/dataset_loaders.py (OSM, WeatherBench, Urban-KG).
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig()
        self._rng = np.random.default_rng(self.config.seed)
        logger.info("UrbanGraphConstructor initialised with config: %s", self.config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> HeteroData:
        """Return a fully constructed HeteroData graph."""
        if self.config.use_toy_data:
            from data.toy_dataset import load_toy_graph
            return load_toy_graph(self.config.toy_data_path)
        data = HeteroData()
        self._add_nodes(data)
        self._add_edges(data)
        if self.config.normalize_features:
            self._normalize(data)
        logger.info("Graph built: %s", self._summary(data))
        return data

    # ------------------------------------------------------------------
    # Node construction
    # ------------------------------------------------------------------

    def _add_nodes(self, data: HeteroData) -> None:
        counts = {
            "power":    self.config.num_power,
            "hospital": self.config.num_hospital,
            "road":     self.config.num_road,
            "citizen":  self.config.num_citizen,
        }
        for ntype, n in counts.items():
            dim = FEATURE_DIMS[ntype]
            feats = self._rng.random((n, dim)).astype(np.float32)

            # Inject structured semantics
            if ntype == "power":
                feats[:, 0] = self._rng.uniform(50, 500, n)   # MW capacity
                feats[:, 1] = self._rng.uniform(0.3, 0.95, n) # load ratio
            elif ntype == "road":
                feats[:, 2] = self._rng.beta(2, 5, n)          # damage score [0,1]

            data[ntype].x = torch.from_numpy(feats)
            data[ntype].num_nodes = n

    # ------------------------------------------------------------------
    # Edge construction (sparse COO format)
    # ------------------------------------------------------------------

    def _add_edges(self, data: HeteroData) -> None:
        counts = {
            "power":    self.config.num_power,
            "hospital": self.config.num_hospital,
            "road":     self.config.num_road,
            "citizen":  self.config.num_citizen,
        }
        for src_type, rel, dst_type in EDGE_TYPES:
            n_src = counts[src_type]
            n_dst = counts[dst_type]
            max_edges = n_src * n_dst
            n_edges = max(1, int(max_edges * self.config.edge_density))

            src_idx = self._rng.integers(0, n_src, n_edges)
            dst_idx = self._rng.integers(0, n_dst, n_edges)
            edge_index = torch.tensor(
                np.stack([src_idx, dst_idx], axis=0), dtype=torch.long
            )

            # Edge attributes: [mu, nu, weight, temporal_decay]
            mu  = self._rng.random(n_edges).astype(np.float32)
            nu  = (1.0 - mu) * self._rng.random(n_edges).astype(np.float32)
            w   = self._rng.random(n_edges).astype(np.float32)
            tau = self._rng.random(n_edges).astype(np.float32)
            edge_attr = torch.from_numpy(np.stack([mu, nu, w, tau], axis=1))

            data[src_type, rel, dst_type].edge_index = edge_index
            data[src_type, rel, dst_type].edge_attr  = edge_attr

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalize(self, data: HeteroData) -> None:
        for ntype in NODE_TYPES:
            if hasattr(data[ntype], "x"):
                x = data[ntype].x
                std, mean = torch.std_mean(x, dim=0, keepdim=True)
                data[ntype].x = (x - mean) / (std + 1e-8)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _summary(data: HeteroData) -> str:
        parts = []
        for ntype in NODE_TYPES:
            if hasattr(data[ntype], "num_nodes"):
                parts.append(f"{ntype}={data[ntype].num_nodes}")
        return " | ".join(parts)
