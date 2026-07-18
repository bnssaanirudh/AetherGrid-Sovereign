import numpy as np
from typing import List, Dict, Any, Optional
from aethergrid_core.schemas import InterventionCandidate

class InterventionEngine:
    @staticmethod
    def apply_intervention(graph_nodes: Dict[str, Any], graph_edges: List[Dict[str, Any]], intervention: InterventionCandidate) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Applies a specific intervention on the graph.
        Returns the modified nodes and edges.
        """
        nodes_copy = {k: v.copy() for k, v in graph_nodes.items()}
        edges_copy = [e.copy() for e in graph_edges]
        
        node_id = intervention.node_id
        action = intervention.action
        
        if node_id not in nodes_copy:
            return nodes_copy, edges_copy
            
        if action == "remove":
            del nodes_copy[node_id]
            edges_copy = [e for e in edges_copy if e['src'] != node_id and e['dst'] != node_id]
        elif action == "isolate":
            edges_copy = [e for e in edges_copy if e['src'] != node_id and e['dst'] != node_id]
        elif action == "reinforce":
            if 'features' in nodes_copy[node_id]:
                # Decrease hesitation/vulnerability feature if it exists, placeholder logic
                nodes_copy[node_id]['features']['vulnerability'] = max(0.0, nodes_copy[node_id].get('features', {}).get('vulnerability', 0.5) - 0.2)
        elif action == "repair":
            if 'features' in nodes_copy[node_id]:
                nodes_copy[node_id]['features']['status'] = 'operational'
                
        return nodes_copy, edges_copy

    @staticmethod
    def expected_cascade_reduction(baseline_size: float, predicted_size_with_intervention: float) -> float:
        """Units: Count/Size reduction"""
        return max(0.0, baseline_size - predicted_size_with_intervention)

    @staticmethod
    def dcg_at_k(relevances: List[float], k: int) -> float:
        relevances = np.asfarray(relevances)[:k]
        if relevances.size:
            return np.sum(relevances / np.log2(np.arange(2, relevances.size + 2)))
        return 0.0

    @staticmethod
    def ndcg_at_k(predicted_scores: List[float], true_reductions: List[float], k: int) -> float:
        """
        Calculates NDCG@K for intervention ranking.
        Aggregation: per-event. Units: Dimensionless (0-1).
        """
        # Sort true reductions based on predicted scores
        order = np.argsort(predicted_scores)[::-1]
        ranked_true = np.array(true_reductions)[order]
        
        ideal_order = np.argsort(true_reductions)[::-1]
        ideal_true = np.array(true_reductions)[ideal_order]
        
        dcg = InterventionEngine.dcg_at_k(ranked_true.tolist(), k)
        idcg = InterventionEngine.dcg_at_k(ideal_true.tolist(), k)
        
        if idcg == 0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def top_k_regret(predicted_scores: List[float], true_reductions: List[float], k: int) -> float:
        """
        Calculates Top-K Regret: Max possible reduction - Max reduction in top K predicted.
        Aggregation: per-event. Units: Cascade Size.
        """
        order = np.argsort(predicted_scores)[::-1][:k]
        best_predicted_reduction = max([true_reductions[i] for i in order]) if len(order) > 0 else 0.0
        best_possible_reduction = max(true_reductions) if true_reductions else 0.0
        return max(0.0, best_possible_reduction - best_predicted_reduction)
