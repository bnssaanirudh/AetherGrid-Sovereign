"""
hgt_model.py
------------
AetherHGT — Heterogeneous Graph Transformer with Quantum-Fuzzy Attention.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple, List, Optional, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import HeteroData

from .hgt_conv import QFHGTConv
from .hgt_readout import make_failure_readout
from .model_utils import count_parameters

logger = logging.getLogger(__name__)

# Fallbacks for legacy/default structures
DEFAULT_NODE_TYPES = ["power", "hospital", "road", "citizen"]
DEFAULT_EDGE_TYPES = [
    ("power", "supplies", "hospital"),
    ("power", "energizes", "road"),
    ("road", "connects", "citizen"),
    ("hospital", "serves", "citizen"),
    ("citizen", "occupies", "road"),
    ("power", "links", "power"),
    ("road", "intersects", "road"),
]
DEFAULT_FEATURE_DIMS = {
    "power": 16,
    "hospital": 12,
    "road": 10,
    "citizen": 8,
}


class AetherHGT(nn.Module):
    """
    Quantum-Fuzzy Heterogeneous Graph Transformer.
    """

    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        dropout: float = 0.1,
        quantize: bool = False,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[Tuple[str, str, str]]] = None,
        feature_dims: Optional[Dict[str, int]] = None,
        fuzzy_family: Literal["IFS", "PFS"] = "IFS",
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.quantize = quantize
        self.node_types = node_types or DEFAULT_NODE_TYPES
        self.edge_types = edge_types or DEFAULT_EDGE_TYPES
        self.feature_dims = feature_dims or DEFAULT_FEATURE_DIMS

        # Input projections
        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(self.feature_dims[ntype], hidden_dim)
            for ntype in self.node_types
        })
        self.input_dropout = nn.Dropout(dropout)

        # QF-HGT layers
        self.conv_layers = nn.ModuleList([
            QFHGTConv(
                hidden_dim=hidden_dim,
                num_heads=num_heads,
                node_types=self.node_types,
                edge_types=self.edge_types,
                dropout=dropout,
                fuzzy_family=fuzzy_family,
            )
            for _ in range(num_layers)
        ])

        # Readout heads
        self.readout = nn.ModuleDict({
            ntype: make_failure_readout(hidden_dim, dropout) for ntype in self.node_types
        })

        if quantize:
            self._apply_quantization()

        logger.info(
            "AetherHGT initialised | layers=%d | heads=%d | dim=%d | quant=%s | family=%s",
            num_layers, num_heads, hidden_dim, quantize, fuzzy_family
        )

    def forward(
        self,
        data: HeteroData,
        return_attention: bool = False,
    ) -> Tuple[Dict[str, Tensor], List[Dict]]:
        device = next(self.parameters()).device

        x_dict: Dict[str, Tensor] = {}
        for ntype in self.node_types:
            if hasattr(data[ntype], "x"):
                x = data[ntype].x.to(device)
                x_dict[ntype] = self.input_dropout(
                    F.gelu(self.input_proj[ntype](x))
                )
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        layer_diagnostics = []
        for layer in self.conv_layers:
            x_dict, diag = layer(x_dict, data, return_attention=return_attention)
            if return_attention:
                layer_diagnostics.append(diag)

        failure_probs: Dict[str, Tensor] = {}
        for ntype in self.node_types:
            failure_probs[ntype] = self.readout[ntype](x_dict[ntype])

        return failure_probs, layer_diagnostics

    def count_parameters(self) -> int:
        return count_parameters(self)

    def _apply_quantization(self) -> None:
        self.quant   = torch.quantization.QuantStub()
        self.dequant = torch.quantization.DeQuantStub()
        logger.info("Quantization stubs attached (8-bit mode).")
