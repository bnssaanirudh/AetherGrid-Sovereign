"""
baselines.py
------------
Implementation of baseline models and adapters for cascading failure prediction.
"""

from __future__ import annotations

import math
import logging
from typing import Dict, List, Tuple, Optional, Literal, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import HeteroData
from torch_geometric.nn import GCNConv, SAGEConv, GATConv, HGTConv, HeteroConv

from .multi_task_heads import MultiTaskHead
from .hgt_model import DEFAULT_NODE_TYPES, DEFAULT_EDGE_TYPES, DEFAULT_FEATURE_DIMS
from .hgt_conv import QFHGTConv

logger = logging.getLogger(__name__)


class HeteroGNNBaseline(nn.Module):
    """
    Standard GNN baseline (GCN, GraphSAGE, GAT) wrapped for heterogeneous urban graphs.
    """
    def __init__(
        self,
        gnn_type: Literal["gcn", "sage", "gat"] = "gcn",
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        dropout: float = 0.1,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[Tuple[str, str, str]]] = None,
        feature_dims: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.gnn_type = gnn_type
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.node_types = node_types or DEFAULT_NODE_TYPES
        self.edge_types = edge_types or DEFAULT_EDGE_TYPES
        self.feature_dims = feature_dims or DEFAULT_FEATURE_DIMS

        # Input projections
        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(self.feature_dims[ntype], hidden_dim)
            for ntype in self.node_types
        })
        self.input_dropout = nn.Dropout(dropout)

        # Build heterogeneous conv layers
        self.conv_layers = nn.ModuleList()
        for _ in range(num_layers):
            convs = {}
            for src_type, rel, dst_type in self.edge_types:
                rel_name = (src_type, rel, dst_type)
                if gnn_type == "gcn":
                    convs[rel_name] = GCNConv(hidden_dim, hidden_dim, add_self_loops=False)
                elif gnn_type == "sage":
                    convs[rel_name] = SAGEConv(hidden_dim, hidden_dim)
                elif gnn_type == "gat":
                    convs[rel_name] = GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, dropout=dropout, add_self_loops=False)
            self.conv_layers.append(HeteroConv(convs, aggr="mean"))

        # Multi-task heads
        self.multi_task_head = MultiTaskHead(hidden_dim, dropout)

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
                x_dict[ntype] = self.input_dropout(F.gelu(self.input_proj[ntype](x)))
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        # Apply conv layers
        for conv in self.conv_layers:
            # We filter edge_index dict based on what actually exists in data
            edge_index_dict = {}
            for src, rel, dst in self.edge_types:
                store = data[src, rel, dst]
                if hasattr(store, "edge_index") and store.edge_index.size(1) > 0:
                    edge_index_dict[(src, rel, dst)] = store.edge_index.to(device)

            x_dict = conv(x_dict, edge_index_dict)
            # Re-apply activations/dropout
            x_dict = {nt: F.gelu(x) for nt, x in x_dict.items()}

        # Pool graph embedding
        all_embs = torch.cat([x_dict[nt] for nt in self.node_types if x_dict[nt].size(0) > 0], dim=0)
        graph_emb = all_embs.mean(dim=0).unsqueeze(0) if all_embs.size(0) > 0 else torch.zeros(1, self.hidden_dim, device=device)
        
        predictions = self.multi_task_head(graph_emb, x_dict)
        return predictions, []


class VanillaHGTBaseline(nn.Module):
    """
    Standard Heterogeneous Graph Transformer (Vanilla HGT) baseline.
    """
    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        dropout: float = 0.1,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[Tuple[str, str, str]]] = None,
        feature_dims: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.node_types = node_types or DEFAULT_NODE_TYPES
        self.edge_types = edge_types or DEFAULT_EDGE_TYPES
        self.feature_dims = feature_dims or DEFAULT_FEATURE_DIMS

        # Input projections
        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(self.feature_dims[ntype], hidden_dim)
            for ntype in self.node_types
        })
        self.input_dropout = nn.Dropout(dropout)

        # Standard PyG HGT Conv layers
        metadata = (self.node_types, self.edge_types)
        self.conv_layers = nn.ModuleList([
            HGTConv(hidden_dim, hidden_dim, metadata, num_heads)
            for _ in range(num_layers)
        ])

        self.multi_task_head = MultiTaskHead(hidden_dim, dropout)

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
                x_dict[ntype] = self.input_dropout(F.gelu(self.input_proj[ntype](x)))
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        edge_index_dict = {}
        for src, rel, dst in self.edge_types:
            store = data[src, rel, dst]
            if hasattr(store, "edge_index") and store.edge_index.size(1) > 0:
                edge_index_dict[(src, rel, dst)] = store.edge_index.to(device)

        for conv in self.conv_layers:
            x_dict = conv(x_dict, edge_index_dict)
            x_dict = {nt: F.gelu(x) for nt, x in x_dict.items()}

        all_embs = torch.cat([x_dict[nt] for nt in self.node_types if x_dict[nt].size(0) > 0], dim=0)
        graph_emb = all_embs.mean(dim=0).unsqueeze(0) if all_embs.size(0) > 0 else torch.zeros(1, self.hidden_dim, device=device)
        
        predictions = self.multi_task_head(graph_emb, x_dict)
        return predictions, []


class TemporalGNNBaseline(nn.Module):
    """
    Temporal GNN baseline that scales messages by exponential time-decay and aggregates with GRU.
    """
    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        dropout: float = 0.1,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[Tuple[str, str, str]]] = None,
        feature_dims: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.node_types = node_types or DEFAULT_NODE_TYPES
        self.edge_types = edge_types or DEFAULT_EDGE_TYPES
        self.feature_dims = feature_dims or DEFAULT_FEATURE_DIMS

        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(self.feature_dims[ntype], hidden_dim)
            for ntype in self.node_types
        })
        self.input_dropout = nn.Dropout(dropout)

        # Build temporal decays and simple message projection per edge type
        self.msg_projs = nn.ModuleDict()
        for src, rel, dst in self.edge_types:
            key = f"{src}__{rel}__{dst}"
            self.msg_projs[key] = nn.Linear(hidden_dim, hidden_dim)

        self.gru = nn.ModuleDict({
            ntype: nn.GRUCell(hidden_dim, hidden_dim)
            for ntype in self.node_types
        })

        self.multi_task_head = MultiTaskHead(hidden_dim, dropout)

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
                x_dict[ntype] = self.input_dropout(F.gelu(self.input_proj[ntype](x)))
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        # Message passing with time decay
        for _ in range(self.num_layers):
            agg_dict = {nt: [] for nt in self.node_types}
            for src, rel, dst in self.edge_types:
                key = f"{src}__{rel}__{dst}"
                store = data[src, rel, dst]
                if not hasattr(store, "edge_index") or store.edge_index.size(1) == 0:
                    continue

                edge_index = store.edge_index.to(device)
                src_nodes, dst_nodes = edge_index[0], edge_index[1]

                # Exponential time decay based on staleness/decay term
                # Assume col 3 of edge_attr is decay/staleness if exists, else default 0
                if hasattr(store, "edge_attr") and store.edge_attr is not None and store.edge_attr.size(1) > 3:
                    tau = store.edge_attr[:, 3:4].to(device)
                    decay = torch.exp(-tau)
                else:
                    decay = torch.ones(edge_index.size(1), 1, device=device)

                msgs = self.msg_projs[key](x_dict[src][src_nodes]) * decay
                
                # Scatter sum messages
                agg = torch.zeros(x_dict[dst].size(0), self.hidden_dim, device=device)
                agg.scatter_add_(0, dst_nodes.unsqueeze(-1).expand_as(msgs), msgs)
                agg_dict[dst].append(agg)

            # GRU update
            for nt in self.node_types:
                if agg_dict[nt]:
                    agg_fused = torch.stack(agg_dict[nt], dim=0).mean(dim=0)
                else:
                    agg_fused = torch.zeros_like(x_dict[nt])
                x_dict[nt] = self.gru[nt](agg_fused, x_dict[nt])

        all_embs = torch.cat([x_dict[nt] for nt in self.node_types if x_dict[nt].size(0) > 0], dim=0)
        graph_emb = all_embs.mean(dim=0).unsqueeze(0) if all_embs.size(0) > 0 else torch.zeros(1, self.hidden_dim, device=device)

        predictions = self.multi_task_head(graph_emb, x_dict)
        return predictions, []


class PhysicsPercolationBaseline(nn.Module):
    """
    Non-neural baseline implementing a standard cascading threshold/percolation model.
    """
    def __init__(self, threshold: float = 0.5, max_steps: int = 5) -> None:
        super().__init__()
        self.threshold = threshold
        self.max_steps = max_steps
        # Stub parameter so optimizer does not complain about empty parameters
        self.dummy_param = nn.Parameter(torch.zeros(1))

    def forward(
        self,
        data: HeteroData,
        return_attention: bool = False,
    ) -> Tuple[Dict[str, Tensor], List[Dict]]:
        # Run a simple threshold percolation process on the graph
        device = self.dummy_param.device
        
        # Build node id mappings to track status
        node_status = {}
        for nt in data.node_types:
            n = data[nt].num_nodes if hasattr(data[nt], "num_nodes") else 0
            if n == 0 and hasattr(data[nt], "x"):
                n = data[nt].x.size(0)
            node_status[nt] = torch.zeros(n, device=device)

        # Trigger node is assumed to be index 0 of the first node type that exists
        triggered = False
        for nt in data.node_types:
            if node_status[nt].size(0) > 0:
                node_status[nt][0] = 1.0
                triggered = True
                break

        if triggered:
            for _ in range(self.max_steps):
                updates = {nt: torch.zeros_like(node_status[nt]) for nt in data.node_types}
                for src, rel, dst in data.edge_types:
                    store = data[src, rel, dst]
                    if hasattr(store, "edge_index") and store.edge_index.size(1) > 0:
                        edge_index = store.edge_index.to(device)
                        src_idx, dst_idx = edge_index[0], edge_index[1]
                        
                        # If src node is failed, it contributes to dst node failure
                        # Weight is edge_attr[:, 2] (base weight) or default 1.0
                        if hasattr(store, "edge_attr") and store.edge_attr is not None and store.edge_attr.size(1) > 2:
                            w = store.edge_attr[:, 2].to(device)
                        else:
                            w = torch.ones(edge_index.size(1), device=device)
                            
                        impact = node_status[src][src_idx] * w
                        updates[dst].scatter_add_(0, dst_idx, impact)

                # Check thresholds
                for nt in data.node_types:
                    failed = (updates[nt] >= self.threshold) | (node_status[nt] > 0.5)
                    node_status[nt] = failed.float()

        # Build output structure
        affected_probs = {nt: node_status[nt] for nt in data.node_types}
        
        # Occurrence probability: 1.0 if any node other than trigger fails, else 0.0
        total_failed = sum(node_status[nt].sum().item() for nt in data.node_types)
        occurrence = 1.0 if total_failed > 1 else 0.0
        
        # Horizon logits: short if failed early, else long
        horizon_logits = torch.tensor([[1.0, 0.0, 0.0]], device=device) if occurrence > 0.5 else torch.tensor([[0.0, 0.0, 1.0]], device=device)

        predictions = {
            "occurrence_prob": torch.tensor([occurrence], device=device),
            "predicted_size": torch.tensor([total_failed], device=device),
            "graph_radius": torch.tensor([float(self.max_steps) if occurrence > 0.5 else 0.0], device=device),
            "physical_radius": torch.tensor([float(self.max_steps * 10.0) if occurrence > 0.5 else 0.0], device=device),
            "horizon_logits": horizon_logits,
            "affected_probs": affected_probs
        }
        return predictions, []


class FuzzyGATBaseline(nn.Module):
    """
    Fuzzy GAT baseline where GAT attention coefficients are scaled by fuzzy memberships.
    """
    def __init__(
        self,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4,
        dropout: float = 0.1,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[Tuple[str, str, str]]] = None,
        feature_dims: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.node_types = node_types or DEFAULT_NODE_TYPES
        self.edge_types = edge_types or DEFAULT_EDGE_TYPES
        self.feature_dims = feature_dims or DEFAULT_FEATURE_DIMS

        self.input_proj = nn.ModuleDict({
            ntype: nn.Linear(self.feature_dims[ntype], hidden_dim)
            for ntype in self.node_types
        })
        self.input_dropout = nn.Dropout(dropout)

        # Custom fuzzy attention modules per edge type
        self.gat_convs = nn.ModuleList()
        for _ in range(num_layers):
            convs = {}
            for src, rel, dst in self.edge_types:
                convs[(src, rel, dst)] = GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, dropout=dropout, add_self_loops=False)
            self.gat_convs.append(HeteroConv(convs, aggr="mean"))

        self.multi_task_head = MultiTaskHead(hidden_dim, dropout)

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
                x_dict[ntype] = self.input_dropout(F.gelu(self.input_proj[ntype](x)))
            else:
                n = data[ntype].num_nodes
                x_dict[ntype] = torch.zeros(n, self.hidden_dim, device=device)

        # Custom message-passing modulating attention by fuzzy weight
        for conv in self.gat_convs:
            edge_index_dict = {}
            for src, rel, dst in self.edge_types:
                store = data[src, rel, dst]
                if hasattr(store, "edge_index") and store.edge_index.size(1) > 0:
                    edge_index_dict[(src, rel, dst)] = store.edge_index.to(device)

            # Standard GAT forward
            x_dict = conv(x_dict, edge_index_dict)
            
            # Modulate outputs by average fuzzy membership
            for nt in self.node_types:
                # Multiply by a dummy factor derived from edge attrs of incoming relations
                mu_val = 1.0
                for src, rel, dst in self.edge_types:
                    if dst == nt:
                        store = data[src, rel, dst]
                        if hasattr(store, "edge_attr") and store.edge_attr is not None and store.edge_attr.size(1) > 0:
                            mu_val = float(store.edge_attr[:, 0].mean().item())
                x_dict[nt] = F.gelu(x_dict[nt]) * (0.5 + 0.5 * mu_val)

        all_embs = torch.cat([x_dict[nt] for nt in self.node_types if x_dict[nt].size(0) > 0], dim=0)
        graph_emb = all_embs.mean(dim=0).unsqueeze(0) if all_embs.size(0) > 0 else torch.zeros(1, self.hidden_dim, device=device)

        predictions = self.multi_task_head(graph_emb, x_dict)
        return predictions, []
