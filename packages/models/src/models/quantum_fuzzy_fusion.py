"""
quantum_fuzzy_fusion.py
-----------------------
Implements the complete Quantum-Fuzzy Attention fusion block.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .fuzzy_attention import IntuitionisticFuzzyAttention


class QuantumFuzzyFusion(nn.Module):
    """
    Full QF-fusion block used inside each HGT convolution layer.
    """

    def __init__(
        self,
        src_dim: int,
        dst_dim: int,
        out_dim: int,
        num_heads: int = 4,
        use_entropy_penalty: bool = True,
        dropout: float = 0.1,
        fuzzy_family: Literal["IFS", "PFS"] = "IFS",
    ) -> None:
        super().__init__()
        if out_dim % num_heads != 0:
            raise ValueError("out_dim must be divisible by num_heads")
        self.out_dim = out_dim
        self.num_heads = num_heads
        self.head_dim = out_dim // num_heads
        self.use_entropy_penalty = use_entropy_penalty

        # Project source features to key/value
        self.lin_src_k = nn.Linear(src_dim, out_dim, bias=False)
        self.lin_src_v = nn.Linear(src_dim, out_dim, bias=False)

        # Project destination features to query
        self.lin_dst_q = nn.Linear(dst_dim, out_dim, bias=False)

        # IFS attention scorer
        self.ifs_attn = IntuitionisticFuzzyAttention(
            in_dim=out_dim,
            num_heads=num_heads,
            dropout=dropout,
            fuzzy_family=fuzzy_family,
        )

        # Output projection
        self.lin_out = nn.Linear(out_dim, out_dim)
        self.layer_norm = nn.LayerNorm(out_dim)
        self.dropout = nn.Dropout(dropout)

        self._reset_parameters()

    def _reset_parameters(self) -> None:
        for lin in [self.lin_src_k, self.lin_src_v, self.lin_dst_q, self.lin_out]:
            nn.init.xavier_uniform_(lin.weight)

    def forward(
        self,
        x_src: Tensor,       # [N_src, src_dim]
        x_dst: Tensor,       # [N_dst, dst_dim]
        edge_index: Tensor,  # [2, E]
        edge_attr: Tensor,   # [E, 4]
    ) -> Tuple[Tensor, Dict[str, Tensor]]:
        N_dst = x_dst.size(0)
        src_idx, dst_idx = edge_index[0], edge_index[1]

        K = self.lin_src_k(x_src)   # [N_src, D]
        V = self.lin_src_v(x_src)   # [N_src, D]
        Q = self.lin_dst_q(x_dst)   # [N_dst, D]

        attn_weights, (mu, nu, pi) = self.ifs_attn(
            query=Q, key=K,
            edge_index=edge_index,
            edge_attr=edge_attr,
        )  # attn_weights: [E, H]

        if self.use_entropy_penalty:
            eps = 1e-8
            H_pi = (
                -pi * torch.log(pi + eps)
                - (1.0 - pi) * torch.log(1.0 - pi + eps)
            ) / math.log(2.0)
            attn_weights = attn_weights * (1.0 - H_pi)

        V_h = V.view(-1, self.num_heads, self.head_dim)  # [N_src, H, d]
        v_e = V_h[src_idx]                               # [E, H, d]
        weighted = v_e * attn_weights.unsqueeze(-1)       # [E, H, d]

        agg = torch.zeros(
            N_dst, self.num_heads, self.head_dim,
            device=x_dst.device, dtype=x_dst.dtype,
        )
        idx_expand = dst_idx.view(-1, 1, 1).expand_as(weighted)
        agg.scatter_add_(0, idx_expand, weighted)
        agg = agg.view(N_dst, -1)   # [N_dst, out_dim]

        out = self.lin_out(self.dropout(agg))
        out = self.layer_norm(out + x_dst[:, :self.out_dim]
                              if x_dst.size(-1) == self.out_dim else out)

        diagnostics = {
            "mu": mu.detach(),
            "nu": nu.detach(),
            "pi": pi.detach(),
            "attn_weights": attn_weights.detach(),
        }
        return out, diagnostics
