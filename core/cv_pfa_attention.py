"""
cv_pfa_attention.py
-------------------
Complex-Valued Pythagorean/Intuitionistic Fuzzy Attention (CV-PFA).
Implements relation-aware heterogeneous attention with native complex tensors.
"""

from __future__ import annotations

import math
from typing import Tuple, Dict, Any, Optional

import torch
import torch.nn as nn
from torch import Tensor
from torch_geometric.utils import softmax

class CVPFAAttention(nn.Module):
    """
    Complex-Valued Fuzzy Attention.
    Uses native complex tensors for the transformation z = rho * exp(i * theta).
    
    Contains two explicit channels:
    - Topology channel: minimum contribution bounded, phase is uncertainty-conditioned.
    - Confidence channel: attenuated based on reliability (mu).
    """
    def __init__(
        self,
        in_dim: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        topology_min_bound: float = 0.1,
        mixed_precision_fallback: bool = True,
    ) -> None:
        super().__init__()
        assert in_dim % num_heads == 0
        self.in_dim = in_dim
        self.num_heads = num_heads
        self.head_dim = in_dim // num_heads
        self.dropout = nn.Dropout(p=dropout)
        self.topology_min_bound = topology_min_bound
        self.mixed_precision_fallback = mixed_precision_fallback

        # Q/K/V projections per relation are typically handled in the Conv layer,
        # but we can do base attention computation here.
        # We assume Q and K are already projected by relation-specific weights.
        self.scale = 1.0 / math.sqrt(self.head_dim)

    def forward(
        self,
        query: Tensor,          # [N_dst, H, d]
        key: Tensor,            # [N_src, H, d]
        value: Tensor,          # [N_src, H, d]
        edge_index: Tensor,     # [2, E]
        mu: Tensor,             # [E, 1]
        nu: Tensor,             # [E, 1]
        pi: Tensor,             # [E, 1]
        theta: Tensor,          # [E, H] or [E, 1]
        N_dst: int,
    ) -> Tuple[Tensor, Dict[str, Any]]:
        """
        Returns
        -------
        agg_msg : [N_dst, H, d] (Complex or Real depending on mode, usually Real out for aggregation)
        diagnostics : Dict with attention stats
        """
        src_idx, dst_idx = edge_index[0], edge_index[1]
        
        # 1. Base Real-Valued Similarity
        q_e = query[dst_idx] # [E, H, d]
        k_e = key[src_idx]   # [E, H, d]
        v_e = value[src_idx] # [E, H, d]
        
        base_score = (q_e * k_e).sum(dim=-1) * self.scale # [E, H]

        # 2. Complex Channels Construction
        # Topology channel: r_top is bounded below, preserving uncertain topology paths
        # Ensure mu is broadcastable
        mu_h = mu.expand(-1, self.num_heads) if mu.size(-1) == 1 else mu
        
        r_top = torch.clamp(mu_h, min=self.topology_min_bound)
        # Convert theta to complex phase: exp(i * theta)
        # Using native complex64
        # Note: if mixed_precision_fallback and dtype is float16, we cast to float32 for complex operations
        orig_dtype = base_score.dtype
        if orig_dtype in (torch.float16, torch.bfloat16) and self.mixed_precision_fallback:
            calc_dtype = torch.float32
        else:
            calc_dtype = orig_dtype
            
        r_top = r_top.to(calc_dtype)
        theta_calc = theta.to(calc_dtype)
        if theta_calc.size(-1) == 1:
            theta_calc = theta_calc.expand(-1, self.num_heads)
            
        z_top = torch.polar(r_top, theta_calc) # [E, H] complex

        # Confidence channel: r_conf is attenuated by reliability mu, phase 0
        r_conf = mu_h.to(calc_dtype)
        z_conf = torch.polar(r_conf, torch.zeros_like(theta_calc)) # [E, H] complex
        
        # 3. Fuse channels with base score
        # Z_total = base_score * (z_top + z_conf)
        # Using complex arithmetic
        base_score_c = base_score.to(calc_dtype).to(torch.complex64)
        z_fused = base_score_c * (z_top + z_conf)
        
        # 4. Convert complex fused score back to real for softmax (e.g. using magnitude)
        # Or compute sparse softmax on magnitude, and multiply value by complex phase.
        # Let's take the magnitude for attention weights:
        attn_mag = torch.abs(z_fused) # [E, H]
        
        # Softmax over destinations
        attn_weights = softmax(attn_mag, dst_idx, num_nodes=N_dst) # [E, H]
        attn_weights = self.dropout(attn_weights)
        
        # Multiply Values by complex attention phase and weights
        # z_fused_phase = exp(i * angle(z_fused))
        z_phase = z_fused / (attn_mag + 1e-8)
        
        # We need to modulate V. We can cast V to complex, multiply, and take real part, 
        # or just use real part as readout.
        v_c = v_e.to(calc_dtype).to(torch.complex64)
        
        # attn_weights is real, z_phase is complex, v_c is complex
        weighted_v_c = v_c * attn_weights.unsqueeze(-1).to(calc_dtype) * z_phase.unsqueeze(-1)
        
        # Readout: stable complex-to-real aggregation. 
        # For simplicity and stability, we take the real part as the hidden path readout.
        weighted_v_real = weighted_v_c.real.to(orig_dtype)
        
        # Scatter sum to destinations
        agg = torch.zeros(
            N_dst, self.num_heads, self.head_dim,
            device=weighted_v_real.device, dtype=orig_dtype
        )
        idx_expand = dst_idx.view(-1, 1, 1).expand_as(weighted_v_real)
        agg.scatter_add_(0, idx_expand, weighted_v_real)
        
        # Diagnostics
        diagnostics = {
            "topology_mag_mean": r_top.mean().item(),
            "confidence_mag_mean": r_conf.mean().item(),
            "attn_entropy": self._compute_entropy(attn_weights, dst_idx, N_dst)
        }
        
        return agg, diagnostics

    def _compute_entropy(self, attn: Tensor, dst_idx: Tensor, N_dst: int) -> float:
        """Compute average entropy of attention distributions."""
        eps = 1e-8
        # -sum(p * log(p))
        entropy = - (attn * torch.log(attn + eps)).sum(dim=-1) # [E]
        # Average per node? We can just take mean over all edges for a fast diagnostic
        return entropy.mean().item()
