"""
hgt_model.py
------------
AetherHGT — Heterogeneous Graph Transformer with Quantum-Fuzzy Attention.
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import HeteroData

from .cv_hgt_conv import CVPFAConv
from .model_registry import ModelRegistry
from .hgt_readout import make_failure_readout
from .model_utils import count_parameters
from .schema import EDGE_TYPES, FEATURE_DIMS, NODE_TYPES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Full AetherHGT Model
# ---------------------------------------------------------------------------

class AetherHGT(nn.Module):
    """
    Quantum-Fuzzy Heterogeneous Graph Transformer for cascading failure prediction.

    Parameters
    ----------
    hidden_dim : int
        Internal feature dimension (same for all node types after projection).
    num_layers : int
        Number of QF-HGT convolution layers.
    num_heads : int
        Attention heads in each QFF block.
    variant : str
        The model variant from the ModelRegistry (e.g. cv_pfa_analytic, real_hgt).
    dropout : float
        Dropout rate throughout.
    quantize : bool
        If True, applies 8-bit quantization-aware stubs (laptop-efficient mode).
    """

    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        variant: str = "cv_pfa_analytic",
        dropout: float = 0.1,
        quantize: bool = False,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.quantize = quantize
        self.variant = variant

        # ---- Input projections (one per node type) ----
        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(FEATURE_DIMS[ntype], hidden_dim)
            for ntype in NODE_TYPES
        })
        self.input_dropout = nn.Dropout(dropout)

        # ---- QF-HGT layers ----
        variant_kwargs = ModelRegistry.get_variant_kwargs(variant)
        self.conv_layers = nn.ModuleList([
            CVPFAConv(
                hidden_dim=hidden_dim,
                num_heads=num_heads,
                node_types=NODE_TYPES,
                edge_types=EDGE_TYPES,
                dropout=dropout,
                **variant_kwargs
            )
            for _ in range(num_layers)
        ])

        # ---- Readout heads ----
        # Predict P(failure) ∈ [0,1] for each node
        self.readout = nn.ModuleDict({
            ntype: make_failure_readout(hidden_dim, dropout) for ntype in NODE_TYPES
        })

        # ---- Optional quantization stubs ----
        if quantize:
            self._apply_quantization()

        logger.info(
            "AetherHGT initialised | layers=%d | heads=%d | dim=%d | quant=%s",
            num_layers, num_heads, hidden_dim, quantize,
        )

    # ------------------------------------------------------------------

    def forward(
        self,
        data: HeteroData,
        return_attention: bool = False,
    ) -> Tuple[Dict[str, Tensor], List[Dict]]:
        """
        Parameters
        ----------
        data : HeteroData
            Urban graph with node features and edge attributes.

        Returns
        -------
        failure_probs : dict[node_type -> Tensor[N, 1]]
            Predicted cascading failure probabilities per node.
        layer_diagnostics : list of dicts from each conv layer.
        """
        device = next(self.parameters()).device

        # Project inputs to shared hidden space
        x_dict: Dict[str, Tensor] = {}
        for ntype in NODE_TYPES:
            if hasattr(data[ntype], "x"):
                x = data[ntype].x.to(device)
                x_dict[ntype] = self.input_dropout(
                    F.gelu(self.input_proj[ntype](x))
                )
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        # Forward through QF-HGT layers
        layer_diagnostics = []
        for layer in self.conv_layers:
            x_dict, diag = layer(x_dict, data, return_attention=return_attention)
            if return_attention:
                layer_diagnostics.append(diag)

        # Compute failure probabilities
        failure_probs: Dict[str, Tensor] = {}
        for ntype in NODE_TYPES:
            failure_probs[ntype] = self.readout[ntype](x_dict[ntype])

        return failure_probs, layer_diagnostics

    # ------------------------------------------------------------------

    def count_parameters(self) -> int:
        return count_parameters(self)

    def _apply_quantization(self) -> None:
        """
        Attach PyTorch quantization stubs.
        For true 4/8-bit inference, replace with bitsandbytes Linear8bitLt.
        """
        self.quant   = torch.quantization.QuantStub()
        self.dequant = torch.quantization.DeQuantStub()
        logger.info("Quantization stubs attached (8-bit mode).")
