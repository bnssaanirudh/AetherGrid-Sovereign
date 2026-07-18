"""
hgt_conv.py
-----------
QF-HGT convolution layer implementation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import HeteroData

from .quantum_fuzzy_fusion import QuantumFuzzyFusion
from .schema import NodeType, EdgeType


class QFHGTConv(nn.Module):
    """
    Single QF-HGT convolution layer.
    For each edge type, runs a QuantumFuzzyFusion block,
    then aggregates messages at each destination node type.
    """

    def __init__(
        self,
        hidden_dim: int,
        num_heads: int,
        node_types: List[NodeType],
        edge_types: List[EdgeType],
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.node_types = node_types
        self.edge_types = edge_types

        self.qff_blocks = nn.ModuleDict()
        for src_type, rel, dst_type in edge_types:
            key = f"{src_type}__{rel}__{dst_type}"
            self.qff_blocks[key] = QuantumFuzzyFusion(
                src_dim=hidden_dim,
                dst_dim=hidden_dim,
                out_dim=hidden_dim,
                num_heads=num_heads,
                dropout=dropout,
            )

        self.norms = nn.ModuleDict({
            ntype: nn.LayerNorm(hidden_dim) for ntype in node_types
        })

    def forward(
        self,
        x_dict: Dict[str, Tensor],
        data: HeteroData,
        return_attention: bool = False,
    ) -> Tuple[Dict[str, Tensor], Dict[str, Any]]:
        out_dict: Dict[str, List[Tensor]] = {nt: [] for nt in self.node_types}
        all_diagnostics: Dict[str, Any] = {}

        for src_type, rel, dst_type in self.edge_types:
            key = f"{src_type}__{rel}__{dst_type}"
            store = data[src_type, rel, dst_type]

            if not hasattr(store, "edge_index"):
                continue

            device = x_dict[src_type].device
            edge_index = store.edge_index
            edge_attr = store.edge_attr
            if edge_index.device != device:
                edge_index = edge_index.to(device)
            if edge_attr.device != device:
                edge_attr = edge_attr.to(device)

            msg, diag = self.qff_blocks[key](
                x_src=x_dict[src_type],
                x_dst=x_dict[dst_type],
                edge_index=edge_index,
                edge_attr=edge_attr,
            )
            out_dict[dst_type].append(msg)
            if return_attention:
                all_diagnostics[key] = diag

        new_x_dict: Dict[str, Tensor] = {}
        for ntype in self.node_types:
            if out_dict[ntype]:
                stacked = torch.stack(out_dict[ntype], dim=0)
                new_x = stacked.mean(dim=0)
            else:
                new_x = x_dict[ntype]
            new_x_dict[ntype] = self.norms[ntype](
                F.gelu(new_x) + x_dict[ntype]
            )

        return new_x_dict, all_diagnostics
