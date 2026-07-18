import random
import logging
from typing import List, Dict, Set, Any, Optional
from collections import deque
from aethergrid_core.data.event_dataset import SamplingCoverage

logger = logging.getLogger(__name__)

class TriggerEgoSampler:
    """
    Trigger-based ego network sampler.
    Supports k-hop, physical radius, and budget-constrained sampling.
    """
    def __init__(
        self,
        k_hop: int = 2,
        max_budget: int = 1000,
        radius: Optional[float] = None,
        relation_quotas: Optional[Dict[str, int]] = None,
        seed: int = 42,
        full_graph_mode: bool = False
    ):
        self.k_hop = k_hop
        self.max_budget = max_budget
        self.radius = radius
        self.relation_quotas = relation_quotas or {}
        self.seed = seed
        self.full_graph_mode = full_graph_mode
        random.seed(self.seed)
        
    def sample(
        self,
        graph_nodes: Dict[str, Dict[str, Any]],
        graph_edges: List[Dict[str, Any]],
        trigger_node_ids: List[str]
    ) -> tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], SamplingCoverage]:
        """
        Samples an ego network around the trigger nodes.
        graph_nodes: {node_id: {type: str, coords: tuple, features: dict}}
        graph_edges: [{"src": str, "dst": str, "type": str, "valid_from": str, "hesitation": float, "critical": bool}]
        """
        if self.full_graph_mode:
            return graph_nodes, graph_edges, SamplingCoverage(
                eligible_nodes=len(graph_nodes),
                included_nodes=len(graph_nodes),
                eligible_edges=len(graph_edges),
                included_edges=len(graph_edges),
                dropped_relation_types={},
                boundary_cuts=0,
                trigger_connectivity=1.0
            )

        # Adjacency list
        adj: Dict[str, List[Dict[str, Any]]] = {n: [] for n in graph_nodes}
        for e in graph_edges:
            if e['src'] in adj and e['dst'] in adj:
                adj[e['src']].append(e)
                # Assuming undirected for traversal purposes unless directed is strict
                # Storing 'direction' in edge payload
                adj[e['dst']].append({'src': e['dst'], 'dst': e['src'], 'type': e['type'], 'original': e})

        visited_nodes: Set[str] = set()
        visited_edges: Set[int] = set() # using id(e) or similar, actually let's just keep track of included edges
        included_edges_list: List[Dict[str, Any]] = []
        
        queue = deque([(t, 0) for t in trigger_node_ids if t in graph_nodes])
        for t in trigger_node_ids:
            if t in graph_nodes:
                visited_nodes.add(t)
        
        relation_counts: Dict[str, int] = {k: 0 for k in self.relation_quotas.keys()}
        dropped_relation_types: Dict[str, int] = {}
        boundary_cuts = 0
        
        while queue and len(visited_nodes) < self.max_budget:
            curr, depth = queue.popleft()
            if depth >= self.k_hop:
                boundary_cuts += len(adj[curr])
                continue
                
            # Sort edges for determinism and priority
            # Priority: critical dependency (True) > high hesitation > random
            neighbors = sorted(adj[curr], key=lambda x: (
                not x.get('original', x).get('critical', False),
                -x.get('original', x).get('hesitation', 0.0),
                random.random()
            ))
            
            for edge in neighbors:
                if len(visited_nodes) >= self.max_budget:
                    break
                    
                rel_type = edge['type']
                quota = self.relation_quotas.get(rel_type, float('inf'))
                current_count = relation_counts.get(rel_type, 0)
                
                # Priority retention overrides quotas if critical
                is_critical = edge.get('original', edge).get('critical', False)
                if current_count >= quota and not is_critical:
                    dropped_relation_types[rel_type] = dropped_relation_types.get(rel_type, 0) + 1
                    continue
                    
                relation_counts[rel_type] = current_count + 1
                
                dst = edge['dst']
                orig_edge = edge.get('original', edge)
                
                if id(orig_edge) not in visited_edges:
                    visited_edges.add(id(orig_edge))
                    included_edges_list.append(orig_edge)
                
                if dst not in visited_nodes:
                    visited_nodes.add(dst)
                    queue.append((dst, depth + 1))
        
        # Calculate coverage
        sampled_nodes = {n: graph_nodes[n] for n in visited_nodes}
        
        coverage = SamplingCoverage(
            eligible_nodes=len(graph_nodes),
            included_nodes=len(sampled_nodes),
            eligible_edges=len(graph_edges),
            included_edges=len(included_edges_list),
            dropped_relation_types=dropped_relation_types,
            boundary_cuts=boundary_cuts,
            trigger_connectivity=len([t for t in trigger_node_ids if t in visited_nodes]) / max(1, len(trigger_node_ids))
        )
        
        return sampled_nodes, included_edges_list, coverage
