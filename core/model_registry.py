"""
model_registry.py
-----------------
Registry for strictly reproducible AetherHGT variants.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Type
import torch.nn as nn

from .cv_hgt_conv import CVPFAConv
from .schema import NODE_TYPES, EDGE_TYPES

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Registry to manage and instantiate model variants."""
    
    @staticmethod
    def build_conv_layer(
        variant: str,
        hidden_dim: int,
        num_heads: int,
        dropout: float = 0.1
    ) -> nn.Module:
        
        if variant == "real_hgt":
            # Just a standard HGT without fuzzy or complex paths.
            # We can use CVPFAConv with phase='none' and 'IFS' but bypass fuzzy by hardcoding 1s?
            # Actually, let's implement a standard HGT Conv fallback in cv_hgt_conv or use cv_hgt_conv with a 'no-fuzzy' flag.
            # But wait, CVPFAConv can do no-fuzzy if we force mu=1, nu=0, pi=0.
            raise NotImplementedError("Will be mapped via kwargs")
            
        raise ValueError(f"Unknown variant: {variant}")
        
    @staticmethod
    def get_variant_kwargs(variant: str) -> Dict[str, Any]:
        """Returns the kwargs to initialize CVPFAConv for a specific variant."""
        if variant == "real_hgt":
            # standard HGT baseline, no fuzzy, no phase
            return {"fuzzy_family": "PFS", "phase_variant": "none", "ablation": "real_hgt"}
        elif variant == "no_fuzzy_hgt":
            return {"fuzzy_family": "PFS", "phase_variant": "none", "ablation": "no_fuzzy"}
        elif variant == "fuzzy_hgt_no_phase":
            return {"fuzzy_family": "PFS", "phase_variant": "none", "ablation": "none"}
        elif variant == "hard_dropout_hgt":
            return {"fuzzy_family": "PFS", "phase_variant": "none", "ablation": "hard_dropout"}
        elif variant == "cv_pfa_analytic":
            return {"fuzzy_family": "PFS", "phase_variant": "analytic", "ablation": "none"}
        elif variant == "cv_pfa_mlp":
            return {"fuzzy_family": "PFS", "phase_variant": "mlp", "ablation": "none"}
        elif variant == "vqc_cv_pfa":
            return {
                "fuzzy_family": "PFS",
                "phase_variant": "vqc",
                "ablation": "none",
                # Circuit manifest fields (informational; CVPFAConv uses defaults above)
                "_circuit_config": {
                    "num_qubits": 4,
                    "circuit_depth": 2,
                    "backend": "default.qubit",
                    "seed": 42,
                    "pennylane_version": "0.17.0",
                    "analytic_mode": True,
                    "shots": None,
                    "status": "simulated_only",
                    "entangling_pattern": "StronglyEntanglingLayers",
                    "note": "This is a simulated narrow VQC phase generator, not a full quantum computer or quantum urban simulator.",
                },
            }
        else:
            raise ValueError(f"Unknown variant: {variant}")
