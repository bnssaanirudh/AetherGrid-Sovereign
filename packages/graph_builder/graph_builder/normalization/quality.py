"""
quality.py
----------
Generates structural and spatial-temporal data quality validation reports.
"""

from __future__ import annotations

from typing import Any, Dict, List


def generate_quality_report(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    outages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes data quality indicators and returns a validation summary.
    """
    node_ids = [n["id"] for n in nodes]
    unique_nodes = set(node_ids)
    dup_node_count = len(node_ids) - len(unique_nodes)
    
    missing_coords = sum(
        1 for n in nodes if n.get("longitude") is None or n.get("latitude") is None
    )
    
    # Simple component connectivity check
    adj: Dict[str, List[str]] = {n_id: [] for n_id in unique_nodes}
    for e in edges:
        src, dst = e["src"], e["dst"]
        if src in adj and dst in adj:
            adj[src].append(dst)
            adj[dst].append(src)
            
    visited = set()
    components = 0
    for node in unique_nodes:
        if node not in visited:
            components += 1
            # BFS/DFS
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
    return {
        "metrics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "duplicate_node_count": dup_node_count,
            "duplicate_node_rate": float(dup_node_count) / max(1, len(nodes)),
            "missing_coordinates": missing_coords,
            "connected_components_count": components,
            "outage_events": len(outages),
            "observed_outages": sum(1 for o in outages if not o.get("is_synthetic", False)),
            "synthetic_outages": sum(1 for o in outages if o.get("is_synthetic", True)),
        },
        "status": "passed" if dup_node_count == 0 and missing_coords == 0 else "warning"
    }
