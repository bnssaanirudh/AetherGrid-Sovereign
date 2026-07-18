"""Fixed toy graph data for offline demos and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import torch
from torch_geometric.data import HeteroData

from core.schema import NODE_TYPES, EDGE_TYPES


def load_toy_graph(path: str | Path | None = None) -> HeteroData:
    """
    Load a small deterministic HeteroData graph from JSON.

    Parameters
    ----------
    path : str | Path | None
        Optional override path to the toy graph JSON.
    """
    json_path = Path(path) if path else Path(__file__).with_name("toy_graph.json")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    data = HeteroData()
    for ntype in NODE_TYPES:
        feats = torch.tensor(payload["nodes"][ntype], dtype=torch.float32)
        data[ntype].x = feats
        data[ntype].num_nodes = feats.size(0)

    for src_type, rel, dst_type in EDGE_TYPES:
        key = f"{src_type}__{rel}__{dst_type}"
        edge = payload["edges"][key]
        edge_index = torch.tensor(edge["edge_index"], dtype=torch.long)
        edge_attr = torch.tensor(edge["edge_attr"], dtype=torch.float32)
        data[src_type, rel, dst_type].edge_index = edge_index
        data[src_type, rel, dst_type].edge_attr = edge_attr

    return data


def load_toy_nodes() -> Dict[str, torch.Tensor]:
    """Return node feature tensors from the toy graph."""
    data = load_toy_graph()
    return {nt: data[nt].x for nt in NODE_TYPES}
