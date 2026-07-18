"""
fuzzy_attention.py
------------------
Implements the Intuitionistic/Pythagorean Fuzzy Set attention layer.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple, Literal

import torch
import torch.nn as nn
from torch import Tensor
from torch_geometric.utils import softmax


class IntuitionisticFuzzyAttention(nn.Module):
    """
    Drop-in replacement for standard dot-product attention in HGT.
    Supports both IFS and PFS semantics.
    """

    def __init__(
        self,
        in_dim: int,
        num_heads: int = 4,
        theta_init: float = math.pi / 4,
        dropout: float = 0.1,
        fuzzy_family: Literal["IFS", "PFS"] = "IFS",
    ) -> None:
        super().__init__()
        assert in_dim % num_heads == 0, "in_dim must be divisible by num_heads"
        self.in_dim    = in_dim
        self.num_heads = num_heads
        self.head_dim  = in_dim // num_heads
        self.dropout   = nn.Dropout(p=dropout)
        self.fuzzy_family = fuzzy_family

        # Learnable quantum phase-shift per head
        self.theta = nn.Parameter(
            torch.full((num_heads,), theta_init), requires_grad=True
        )

        # Membership/non-membership feature extractors from edge attributes
        self.edge_mu_proj = nn.Linear(4, num_heads, bias=False)
        self.edge_nu_proj = nn.Linear(4, num_heads, bias=False)

        # Standard Q/K projection for base attention
        self.W_q = nn.Linear(in_dim, in_dim, bias=False)
        self.W_k = nn.Linear(in_dim, in_dim, bias=False)

        self._init_weights()

    def _init_weights(self) -> None:
        nn.init.xavier_uniform_(self.W_q.weight)
        nn.init.xavier_uniform_(self.W_k.weight)
        nn.init.xavier_uniform_(self.edge_mu_proj.weight)
        nn.init.xavier_uniform_(self.edge_nu_proj.weight)

    def forward(
        self,
        query: Tensor,          # [N_dst, in_dim]
        key: Tensor,            # [N_src, in_dim]
        edge_index: Tensor,     # [2, E]  (src, dst)
        edge_attr: Tensor,      # [E, 4]  (mu_raw, nu_raw, w, tau)
    ) -> Tuple[Tensor, Tuple[Tensor, Tensor, Tensor]]:
        if edge_attr.dim() != 2 or edge_attr.size(1) != 4:
            raise ValueError("edge_attr must have shape [E, 4]")

        N_dst = query.size(0)
        src_idx, dst_idx = edge_index[0], edge_index[1]

        Q = self.W_q(query)                              # [N_dst, D]
        K = self.W_k(key)                                # [N_src, D]
        Q_h = Q.view(-1, self.num_heads, self.head_dim)  # [N_dst, H, d]
        K_h = K.view(-1, self.num_heads, self.head_dim)  # [N_src, H, d]

        q_e = Q_h[dst_idx]   # [E, H, d]
        k_e = K_h[src_idx]   # [E, H, d]
        base_score = (q_e * k_e).sum(dim=-1) / math.sqrt(self.head_dim)  # [E, H]

        mu_raw = self.edge_mu_proj(edge_attr)         # [E, H]
        nu_raw = self.edge_nu_proj(edge_attr)         # [E, H]

        if self.fuzzy_family == "PFS":
            # Pythagorean Fuzzy Set constraint: mu^2 + nu^2 <= 1
            mu = torch.sigmoid(mu_raw)
            nu = torch.sigmoid(nu_raw) * torch.sqrt(1.0 - mu**2 + 1e-8)
            pi = torch.sqrt(torch.clamp(1.0 - mu**2 - nu**2, min=0.0) + 1e-8)
        else:  # IFS
            mu = torch.sigmoid(mu_raw)
            nu = torch.sigmoid(nu_raw) * (1.0 - mu)
            pi = 1.0 - mu - nu

        cos_theta = torch.cos(self.theta).unsqueeze(0)        # [1, H]
        amplitude = torch.sqrt(
            mu**2 + nu**2 + 2.0 * mu * nu * cos_theta + 1e-8
        )                                                      # [E, H]

        fused_score = base_score * amplitude * (1.0 - pi)     # [E, H]

        attn_weights = softmax(fused_score, dst_idx, num_nodes=N_dst)  # [E, H]
        attn_weights = self.dropout(attn_weights)

        return attn_weights, (mu, nu, pi)
