import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class BoundResult:
    mode: str # 'conservative_analytic', 'empirical_local', 'diagnostic_only'
    computed_bound: float
    observed_outcome: Optional[float]
    coverage_indicator: Optional[bool]
    tightness_ratio: Optional[float]
    layer_lipschitz: List[float]
    relation_operator_norms: Dict[str, float]
    degree_envelope: int
    hesitation_summary: float
    initial_perturbation_norm: float

class CascadeAmplificationBound:
    """
    Computes bounds on cascade amplification based on network topology and empirical Lipschitz constants.
    """
    def __init__(
        self,
        mode: str = "empirical_local",
        layer_lipschitz_estimates: Optional[List[float]] = None,
        relation_operator_norms: Optional[Dict[str, float]] = None
    ):
        self.mode = mode
        # Default empirical estimates if not provided
        self.layer_lipschitz = layer_lipschitz_estimates or [1.2, 1.1]
        self.relation_operator_norms = relation_operator_norms or {"connects": 1.0, "powers": 1.5, "default": 1.0}

    def compute_bound(
        self,
        sampled_nodes: Dict[str, Any],
        sampled_edges: List[Dict[str, Any]],
        initial_perturbation_norm: float,
        observed_outcome: Optional[float] = None
    ) -> BoundResult:
        # Calculate Degree Envelope (max degree in sampled network)
        degrees = {n: 0 for n in sampled_nodes}
        for e in sampled_edges:
            if e['src'] in degrees:
                degrees[e['src']] += 1
            if e['dst'] in degrees:
                degrees[e['dst']] += 1
                
        degree_envelope = max(degrees.values()) if degrees else 0
        
        # Calculate Hesitation Summary (mean hesitation across nodes/edges)
        hesitations = []
        for e in sampled_edges:
            if 'hesitation' in e:
                hesitations.append(e['hesitation'])
        hesitation_summary = float(np.mean(hesitations)) if hesitations else 0.0
        
        # Determine maximum relation operator norm present
        max_op_norm = 1.0
        for e in sampled_edges:
            rel_type = e.get('type', 'default')
            op_norm = self.relation_operator_norms.get(rel_type, self.relation_operator_norms.get("default", 1.0))
            max_op_norm = max(max_op_norm, op_norm)
            
        # Compute the theoretical amplification bound
        # A simple placeholder formula representing the combination of Lipschitz constants, graph structure, and uncertainty
        total_lipschitz = np.prod(self.layer_lipschitz)
        uncertainty_modulation = (1.0 + hesitation_summary)
        
        if self.mode == "conservative_analytic":
            computed_bound = initial_perturbation_norm * total_lipschitz * max_op_norm * (degree_envelope ** len(self.layer_lipschitz)) * uncertainty_modulation
        else: # empirical_local or diagnostic
            # Empirical relies on observed typical scaling rather than strict worst-case
            computed_bound = initial_perturbation_norm * total_lipschitz * max_op_norm * np.sqrt(degree_envelope) * uncertainty_modulation
            
        # Calculate coverage and tightness if observed outcome is present
        coverage = None
        tightness = None
        if observed_outcome is not None:
            coverage = computed_bound >= observed_outcome
            # Tightness ratio: bound / observed (1.0 is perfect, higher is loose)
            # Avoid division by zero
            tightness = computed_bound / observed_outcome if observed_outcome > 1e-5 else (computed_bound / 1e-5)
            
        return BoundResult(
            mode=self.mode,
            computed_bound=float(computed_bound),
            observed_outcome=float(observed_outcome) if observed_outcome is not None else None,
            coverage_indicator=coverage,
            tightness_ratio=float(tightness) if tightness is not None else None,
            layer_lipschitz=self.layer_lipschitz,
            relation_operator_norms=self.relation_operator_norms,
            degree_envelope=degree_envelope,
            hesitation_summary=hesitation_summary,
            initial_perturbation_norm=initial_perturbation_norm
        )
