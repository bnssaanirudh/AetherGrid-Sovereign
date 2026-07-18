"""
cv_hgt_conv.py
--------------
CV-PFA Heterogeneous Graph Convolution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import HeteroData

from .schema import NodeType, EdgeType
from .fuzzy_state import FuzzyStateEncoder
from .phase_generator import AnalyticPhaseGenerator, MLPPhaseGenerator, VQCPhaseGenerator, PhaseGenerator
from .cv_pfa_attention import CVPFAAttention


class CVPFAConv(nn.Module):
    """
    Complex-Valued Pythagorean Fuzzy Attention Convolution.
    """
    def __init__(
        self,
        hidden_dim: int,
        num_heads: int,
        node_types: List[NodeType],
        edge_types: List[EdgeType],
        fuzzy_family: Literal["IFS", "PFS"] = "PFS",
        phase_variant: Literal["analytic", "mlp", "vqc", "none"] = "analytic",
        dropout: float = 0.1,
        ablation: str = "none",
    ) -> None:
        super().__init__()
        self.ablation = ablation
        self.hidden_dim = hidden_dim
        self.node_types = node_types
        self.edge_types = edge_types
        self.phase_variant = phase_variant

        # Node type specific projections (Q, K, V)
        self.k_lin = nn.ModuleDict({nt: nn.Linear(hidden_dim, hidden_dim) for nt in node_types})
        self.v_lin = nn.ModuleDict({nt: nn.Linear(hidden_dim, hidden_dim) for nt in node_types})
        self.q_lin = nn.ModuleDict({nt: nn.Linear(hidden_dim, hidden_dim) for nt in node_types})

        # Relation specific weights
        self.relation_k = nn.ParameterDict()
        self.relation_v = nn.ParameterDict()
        self.edge_embeddings = nn.ParameterDict()
        
        # We assume edge_attr has 4 dims initially (mu_raw, nu_raw, weight, tau)
        self.fuzzy_encoder = FuzzyStateEncoder(in_features=4, fuzzy_family=fuzzy_family, mode="learned")
        
        if phase_variant == "analytic":
            self.phase_gen = AnalyticPhaseGenerator(out_dim=num_heads)
        elif phase_variant == "mlp":
            self.phase_gen = MLPPhaseGenerator(edge_embed_dim=16, node_dim=hidden_dim, out_dim=num_heads)
        elif phase_variant == "vqc":
            # Default to 4 qubits / 2 layers; callers may override via a factory.
            # If PennyLane is absent the constructor sets has_pennylane=False and
            # every forward call transparently falls back to the matched MLP.
            self.phase_gen = VQCPhaseGenerator(
                edge_embed_dim=16,
                node_dim=hidden_dim,
                out_dim=num_heads,
                num_qubits=4,
                circuit_depth=2,
                backend="default.qubit",
                seed=42,
            )
        else:
            self.phase_gen = None

        self.cv_attention = CVPFAAttention(
            in_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
        )

        for src_type, rel, dst_type in edge_types:
            key = f"{src_type}__{rel}__{dst_type}"
            self.relation_k[key] = nn.Parameter(torch.Tensor(num_heads, hidden_dim // num_heads, hidden_dim // num_heads))
            self.relation_v[key] = nn.Parameter(torch.Tensor(num_heads, hidden_dim // num_heads, hidden_dim // num_heads))
            self.edge_embeddings[key] = nn.Parameter(torch.Tensor(16))
            nn.init.xavier_uniform_(self.relation_k[key])
            nn.init.xavier_uniform_(self.relation_v[key])
            nn.init.normal_(self.edge_embeddings[key])

        self.out_lin = nn.ModuleDict({nt: nn.Linear(hidden_dim, hidden_dim) for nt in node_types})
        self.norms = nn.ModuleDict({nt: nn.LayerNorm(hidden_dim) for nt in node_types})
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x_dict: Dict[str, Tensor],
        data: HeteroData,
        return_attention: bool = False,
    ) -> Tuple[Dict[str, Tensor], Dict[str, Any]]:
        
        # Pre-compute Q, K, V for all nodes
        q_dict, k_dict, v_dict = {}, {}, {}
        for nt in self.node_types:
            q_dict[nt] = self.q_lin[nt](x_dict[nt]).view(-1, self.cv_attention.num_heads, self.cv_attention.head_dim)
            k_dict[nt] = self.k_lin[nt](x_dict[nt]).view(-1, self.cv_attention.num_heads, self.cv_attention.head_dim)
            v_dict[nt] = self.v_lin[nt](x_dict[nt]).view(-1, self.cv_attention.num_heads, self.cv_attention.head_dim)

        out_dict: Dict[str, List[Tensor]] = {nt: [] for nt in self.node_types}
        all_diagnostics: Dict[str, Any] = {}

        for src_type, rel, dst_type in self.edge_types:
            key = f"{src_type}__{rel}__{dst_type}"
            store = data[src_type, rel, dst_type]

            if not hasattr(store, "edge_index") or store.edge_index.size(1) == 0:
                continue

            device = x_dict[src_type].device
            edge_index = store.edge_index
            edge_attr = store.edge_attr
            if edge_index.device != device:
                edge_index = edge_index.to(device)
            if edge_attr.device != device:
                edge_attr = edge_attr.to(device)

            E = edge_index.size(1)
            N_dst = x_dict[dst_type].size(0)

            # 1. Fuzzy State
            mu, nu, pi, f_diag = self.fuzzy_encoder(edge_attr)
            
            if hasattr(self, 'ablation'):
                if self.ablation in ("real_hgt", "no_fuzzy"):
                    mu = torch.ones_like(mu)
                    nu = torch.zeros_like(nu)
                    pi = torch.zeros_like(pi)
                elif self.ablation == "hard_dropout":
                    # Hard dropout ablates uncertain edges completely
                    # E.g. drop if mu < 0.5 or pi > 0.3
                    keep_mask = (mu > 0.5) & (pi < 0.3)
                    mu = mu * keep_mask.float()
                    # if mask is 0, we effectively drop the edge contribution
            
            # 2. Phase Generation
            if self.phase_gen is not None:
                edge_emb = self.edge_embeddings[key].unsqueeze(0).expand(E, -1)
                src_state = x_dict[src_type][edge_index[0]]
                dst_state = x_dict[dst_type][edge_index[1]]
                staleness = edge_attr[:, 3:4] if edge_attr.size(1) > 3 else None # Assuming col 3 is tau
                
                theta, p_diag = self.phase_gen(
                    hesitation=pi,
                    staleness=staleness,
                    edge_type_embedding=edge_emb,
                    source_state=src_state,
                    destination_state=dst_state,
                    local_stress=None
                )
            else:
                theta = torch.zeros(E, self.cv_attention.num_heads, device=device)
                p_diag = {}

            # 3. Relation-specific K, V transformation
            k_rel = torch.einsum('ehd,hdc->ehc', k_dict[src_type][edge_index[0]], self.relation_k[key])
            v_rel = torch.einsum('ehd,hdc->ehc', v_dict[src_type][edge_index[0]], self.relation_v[key])
            q_dst = q_dict[dst_type] # [N_dst, H, d]

            # 4. CV-PFA Attention
            # The attention takes full Q and K/V indexed by edge
            # But the signature expects Q full, K/V full and uses edge_index inside.
            # To apply relation specific transform, we pass the transformed edge-wise K/V.
            # Let's adjust input to the CV-PFA forward:
            # Actually, CVPFAAttention does `q_e = query[dst_idx]`, `k_e = key[src_idx]`.
            # Since we applied relation transform to the edge, we bypass that and just pass the edge tensors.
            # To reuse CVPFAAttention cleanly, I'll pass q_dst and k_dict, and modify it or just compute it here.
            # I will modify CVPFAAttention to accept edge-wise inputs for K and V.
            
            # Temporary fix: compute edge-wise Q
            q_e = q_dst[edge_index[1]]
            
            # Need to call cv_attention directly with edge-wise tensors for relation-aware HGT.
            base_score = (q_e * k_rel).sum(dim=-1) * self.cv_attention.scale
            
            mu_h = mu.expand(-1, self.cv_attention.num_heads)
            r_top = torch.clamp(mu_h, min=self.cv_attention.topology_min_bound).to(torch.float32)
            theta_calc = theta.to(torch.float32)
            z_top = torch.polar(r_top, theta_calc)
            z_conf = torch.polar(mu_h.to(torch.float32), torch.zeros_like(theta_calc))
            z_fused = base_score.to(torch.float32).to(torch.complex64) * (z_top + z_conf)
            attn_mag = torch.abs(z_fused)
            
            from torch_geometric.utils import softmax
            attn_weights = softmax(attn_mag, edge_index[1], num_nodes=N_dst)
            attn_weights = self.cv_attention.dropout(attn_weights)
            
            z_phase = z_fused / (attn_mag + 1e-8)
            v_c = v_rel.to(torch.float32).to(torch.complex64)
            weighted_v_c = v_c * attn_weights.unsqueeze(-1) * z_phase.unsqueeze(-1)
            weighted_v_real = weighted_v_c.real
            
            agg = torch.zeros(N_dst, self.cv_attention.num_heads, self.cv_attention.head_dim, device=device)
            agg.scatter_add_(0, edge_index[1].view(-1, 1, 1).expand_as(weighted_v_real), weighted_v_real)
            
            msg = agg.view(N_dst, -1)
            out_dict[dst_type].append(msg)
            
            if return_attention:
                all_diagnostics[key] = {**f_diag, **p_diag, "attn_entropy": self.cv_attention._compute_entropy(attn_weights, edge_index[1], N_dst)}

        new_x_dict: Dict[str, Tensor] = {}
        for ntype in self.node_types:
            if out_dict[ntype]:
                stacked = torch.stack(out_dict[ntype], dim=0)
                new_x = stacked.sum(dim=0) # sum over relations as per standard HGT
            else:
                new_x = torch.zeros_like(x_dict[ntype])
            
            out_proj = self.dropout(self.out_lin[ntype](F.gelu(new_x)))
            new_x_dict[ntype] = self.norms[ntype](out_proj + x_dict[ntype])

        return new_x_dict, all_diagnostics
