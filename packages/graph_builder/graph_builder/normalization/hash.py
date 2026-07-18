"""
hash.py
-------
Order-independent deterministic hashing of heterogeneous graph structures.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List


def compute_deterministic_graph_hash(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> str:
    """
    Computes a stable SHA-256 hash of graph elements independent of their sequence order.
    """
    node_fingerprints = []
    for n in nodes:
        node_payload = f"{n['id']}:{n.get('longitude', 0.0):.6f}:{n.get('latitude', 0.0):.6f}"
        node_fingerprints.append(hashlib.sha256(node_payload.encode("utf-8")).hexdigest())
    
    edge_fingerprints = []
    for e in edges:
        edge_payload = f"{e['src']}->{e['dst']}:{e.get('type', '')}"
        edge_fingerprints.append(hashlib.sha256(edge_payload.encode("utf-8")).hexdigest())
        
    sorted_nodes = sorted(node_fingerprints)
    sorted_edges = sorted(edge_fingerprints)
    
    overall_payload = "|".join(sorted_nodes) + "||" + "|".join(sorted_edges)
    return hashlib.sha256(overall_payload.encode("utf-8")).hexdigest()
