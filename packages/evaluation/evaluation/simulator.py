"""
simulator.py
------------
Simulates structural cascades across the urban infrastructure dependency network
to generate training labels while preserving strict temporal separation (no leakage).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Set, Tuple
import numpy as np
from pydantic import BaseModel, Field


class CascadeGenerationManifest(BaseModel):
    seed: int
    trigger_node: str
    hazard_intensity: float = Field(..., ge=0.0, le=1.0)
    propagation_probability: float = Field(..., ge=0.0, le=1.0)
    vulnerability_threshold: float = Field(..., ge=0.0, le=1.0)
    cascade_size: int
    affected_nodes: List[str]
    physical_radius_meters: float
    graph_radius_hops: int
    provenance_class: str = "semi_synthetic_simulation"


class CascadeSimulator:
    """
    Percolation-based hazard propagation simulator over heterogeneous networks.
    """

    def __init__(
        self,
        seed: int = 42,
        hazard_intensity: float = 0.5,
        propagation_probability: float = 0.4,
        vulnerability_threshold: float = 0.3
    ) -> None:
        self.seed = seed
        self.hazard_intensity = hazard_intensity
        self.propagation_probability = propagation_probability
        self.vulnerability_threshold = vulnerability_threshold
        self._rng = random.Random(seed)

    def run(
        self,
        node_positions: Dict[str, Tuple[float, float]],
        adjacency: Dict[str, List[str]],
        trigger_node: str,
        interventions: Optional[Set[str]] = None
    ) -> Tuple[Dict[str, bool], CascadeGenerationManifest]:
        """
        Runs the simulation cascade starting at trigger_node.
        Returns a dictionary mapping node IDs to failed status (True/False)
        and the simulation manifest.
        """
        self._rng.seed(self.seed)
        interventions = interventions or set()

        failed_nodes: Set[str] = set()
        failure_times: Dict[str, int] = {}
        
        # Initial trigger node failure check
        if trigger_node not in interventions:
            if self.hazard_intensity >= self.vulnerability_threshold:
                failed_nodes.add(trigger_node)
                failure_times[trigger_node] = 0

        # Propagation iterations (percolation)
        active_front = list(failed_nodes)
        hops = 0
        
        while active_front:
            next_front = []
            hops += 1
            for u in active_front:
                for v in adjacency.get(u, []):
                    if v in failed_nodes or v in interventions:
                        continue
                    # Percolation success probability check
                    if self._rng.random() < self.propagation_probability:
                        failed_nodes.add(v)
                        failure_times[v] = hops
                        next_front.append(v)
            active_front = next_front

        # Compute physical and graph radius metrics
        max_dist = 0.0
        if trigger_node in node_positions:
            tx, ty = node_positions[trigger_node]
            for node in failed_nodes:
                if node in node_positions:
                    nx, ny = node_positions[node]
                    dist = math.sqrt((tx - nx)**2 + (ty - ny)**2)
                    if dist > max_dist:
                        max_dist = dist

        # Build output manifest
        manifest = CascadeGenerationManifest(
            seed=self.seed,
            trigger_node=trigger_node,
            hazard_intensity=self.hazard_intensity,
            propagation_probability=self.propagation_probability,
            vulnerability_threshold=self.vulnerability_threshold,
            cascade_size=len(failed_nodes),
            affected_nodes=list(failed_nodes),
            physical_radius_meters=float(max_dist),
            graph_radius_hops=hops - 1 if failed_nodes else 0
        )
        
        # State map output
        failures_map = {n: (n in failed_nodes) for n in node_positions}
        return failures_map, manifest
import math
