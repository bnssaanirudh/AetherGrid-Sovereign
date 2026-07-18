"""
builder.py
----------
Builds heterogeneous graphs conforming to the NodeRecord and EdgeRecord domain schemas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import numpy as np
import torch
from torch_geometric.data import HeteroData

from aethergrid_core import (
    NodeRecord,
    EdgeRecord,
    NodeType,
    RelationType,
    resolve_node_type,
)

logger = logging.getLogger(__name__)

# Proposal and Legacy Mapping
FEATURE_DIMS = {
    "power_node": 16,
    "poi_social_node": 12,
    "road_segment": 10,
    "weather_station": 8,
    "control_response_node": 8,
}


@dataclass
class GraphConfig:
    num_power:    int = 50
    num_hospital: int = 20
    num_road:     int = 200
    num_citizen:  int = 100
    edge_density: float = 0.05
    add_self_loops: bool = False
    normalize_features: bool = True
    seed: int = 42
    use_toy_data: bool = False
    toy_data_path: Optional[str] = None


class UrbanGraphConstructor:
    """
    Constructs the heterogeneous urban infrastructure graph using domain schemas.
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig()
        self._rng = np.random.default_rng(self.config.seed)
        logger.info("UrbanGraphConstructor initialized with config: %s", self.config)

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
        return data

    def _add_nodes(self, data: HeteroData) -> None:
        counts = {
            "power_node": self.config.num_power,
            "poi_social_node": self.config.num_hospital + self.config.num_citizen,
            "road_segment": self.config.num_road,
        }

        # Keep legacy aliases in HeteroData for backward compatibility with HGT
        counts_legacy = {
            "power": self.config.num_power,
            "hospital": self.config.num_hospital,
            "road": self.config.num_road,
            "citizen": self.config.num_citizen,
        }

        for ntype, n in counts_legacy.items():
            resolved = resolve_node_type(ntype)
            dim = FEATURE_DIMS[resolved]
            feats = self._rng.random((n, dim)).astype(np.float32)

            # Structured semantics
            if ntype == "power":
                feats[:, 0] = self._rng.uniform(50, 500, n)
                feats[:, 1] = self._rng.uniform(0.3, 0.95, n)
            elif ntype == "road":
                feats[:, 2] = self._rng.beta(2, 5, n)

            # NodeRecord schema compliance check
            for i in range(n):
                # Ensure spatial CRS is EPSG:4326 by default
                rec = NodeRecord(
                    id=f"{ntype}_{i}",
                    node_type=resolved,
                    is_synthetic=True,
                    source="synthetic_constructor",
                    crs="EPSG:4326",
                    coordinates=(float(self._rng.uniform(-180, 180)), float(self._rng.uniform(-90, 90))),
                    attributes={"MW_capacity": float(feats[i, 0])} if ntype == "power" else {},
                    validation_status="verified",
                )

            data[ntype].x = torch.from_numpy(feats)
            data[ntype].num_nodes = n

    def _add_edges(self, data: HeteroData) -> None:
        from core.schema import EDGE_TYPES
        counts_legacy = {
            "power": self.config.num_power,
            "hospital": self.config.num_hospital,
            "road": self.config.num_road,
            "citizen": self.config.num_citizen,
        }

        for src_type, rel, dst_type in EDGE_TYPES:
            n_src = counts_legacy[src_type]
            n_dst = counts_legacy[dst_type]
            max_edges = n_src * n_dst
            n_edges = max(1, int(max_edges * self.config.edge_density))

            src_idx = self._rng.integers(0, n_src, n_edges)
            dst_idx = self._rng.integers(0, n_dst, n_edges)
            edge_index = torch.tensor(
                np.stack([src_idx, dst_idx], axis=0), dtype=torch.long
            )

            mu  = self._rng.random(n_edges).astype(np.float32)
            nu  = (1.0 - mu) * self._rng.random(n_edges).astype(np.float32)
            w   = self._rng.random(n_edges).astype(np.float32)
            tau = self._rng.random(n_edges).astype(np.float32)
            edge_attr = torch.from_numpy(np.stack([mu, nu, w, tau], axis=1))

            # EdgeRecord validation check
            for i in range(n_edges):
                EdgeRecord(
                    id=f"{src_type}_{src_idx[i]}__{rel}__{dst_type}_{dst_idx[i]}",
                    src_id=f"{src_type}_{src_idx[i]}",
                    dst_id=f"{dst_type}_{dst_idx[i]}",
                    relation="powers" if rel == "supplies" or rel == "energizes" else "connects",
                    is_synthetic=True,
                    source="synthetic_constructor",
                    attributes={"mu": float(mu[i]), "nu": float(nu[i])},
                    validation_status="verified",
                )

            data[src_type, rel, dst_type].edge_index = edge_index
            data[src_type, rel, dst_type].edge_attr  = edge_attr

    def _normalize(self, data: HeteroData) -> None:
        from core.schema import NODE_TYPES
        for ntype in NODE_TYPES:
            if hasattr(data[ntype], "x"):
                x = data[ntype].x
                std, mean = torch.std_mean(x, dim=0, keepdim=True)
                data[ntype].x = (x - mean) / (std + 1e-8)
