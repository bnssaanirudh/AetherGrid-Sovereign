"""
Core schema definitions for node/edge registries and type aliases.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Literal

from torch import Tensor

NodeType = Literal["power", "hospital", "road", "citizen"]
EdgeType = Tuple[NodeType, str, NodeType]
HeteroDict = Dict[str, Tensor]

NODE_TYPES: List[NodeType] = ["power", "hospital", "road", "citizen"]

EDGE_TYPES: List[EdgeType] = [
    ("power", "supplies", "hospital"),
    ("power", "energizes", "road"),
    ("road", "connects", "citizen"),
    ("hospital", "serves", "citizen"),
    ("citizen", "occupies", "road"),
    ("power", "links", "power"),
    ("road", "intersects", "road"),
]

FEATURE_DIMS: Dict[NodeType, int] = {
    "power": 16,
    "hospital": 12,
    "road": 10,
    "citizen": 8,
}
