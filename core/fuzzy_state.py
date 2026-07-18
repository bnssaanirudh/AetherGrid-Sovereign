"""
fuzzy_state.py
--------------
Differentiable modules mapping validated sensor-state features to fuzzy triples
(Intuitionistic or Pythagorean Fuzzy Sets), with explicit diagnostics.
"""

from __future__ import annotations

from typing import Dict, Literal, Tuple, Any

import torch
import torch.nn as nn
from torch import Tensor

FuzzyFamily = Literal["IFS", "PFS"]


class FuzzyStateEncoder(nn.Module):
    """
    Maps raw sensor edge features to a valid Fuzzy Triple (mu, nu, pi).
    Supports Intuitionistic Fuzzy Sets (IFS) and Pythagorean Fuzzy Sets (PFS).

    Parameters
    ----------
    in_features : int
        Number of raw edge features.
    fuzzy_family : FuzzyFamily
        "IFS" (mu + nu <= 1) or "PFS" (mu^2 + nu^2 <= 1).
    mode : str
        "analytic" (direct scaling/sigmoid) or "learned" (MLP mapping).
    """

    def __init__(
        self,
        in_features: int,
        fuzzy_family: FuzzyFamily = "PFS",
        mode: Literal["analytic", "learned"] = "learned",
    ) -> None:
        super().__init__()
        assert fuzzy_family in ("IFS", "PFS"), "fuzzy_family must be 'IFS' or 'PFS'"
        self.in_features = in_features
        self.fuzzy_family = fuzzy_family
        self.mode = mode

        if mode == "learned":
            self.mu_proj = nn.Sequential(
                nn.Linear(in_features, 16),
                nn.ReLU(),
                nn.Linear(16, 1)
            )
            self.nu_proj = nn.Sequential(
                nn.Linear(in_features, 16),
                nn.ReLU(),
                nn.Linear(16, 1)
            )
        else:
            # Analytic mode expects exactly the right inputs (or we take first 2 dims)
            self.mu_proj = nn.Linear(in_features, 1, bias=False)
            self.nu_proj = nn.Linear(in_features, 1, bias=False)
            # Initialize to identity for the first 2 features if analytic
            with torch.no_grad():
                self.mu_proj.weight.fill_(0)
                self.nu_proj.weight.fill_(0)
                if in_features >= 1:
                    self.mu_proj.weight[0, 0] = 1.0
                if in_features >= 2:
                    self.nu_proj.weight[0, 1] = 1.0

    def forward(self, edge_features: Tensor, state_flags: dict[str, Tensor] | None = None) -> Tuple[Tensor, Tensor, Tensor, Dict[str, Any]]:
        """
        Parameters
        ----------
        edge_features : Tensor [E, in_features]
            Raw edge features.
        state_flags : dict[str, Tensor], optional
            Flags for explicit states (missing, stale, contradictory, quarantined).
            Expected shape for each value is [E, 1] boolean or 0/1 float.

        Returns
        -------
        mu, nu, pi : Tensor [E, 1]
            Fuzzy membership, non-membership, and hesitation.
        diagnostics : dict
            Contains counts of violations that required projection.
        """
        mu_raw = self.mu_proj(edge_features)
        nu_raw = self.nu_proj(edge_features)

        # Baseline sigmoid mapping to [0, 1]
        mu = torch.sigmoid(mu_raw)
        nu = torch.sigmoid(nu_raw)

        # Handle explicit states if provided
        if state_flags is not None:
            if "missing" in state_flags:
                mask = state_flags["missing"].bool()
                mu = torch.where(mask, torch.zeros_like(mu), mu)
                nu = torch.where(mask, torch.zeros_like(nu), nu)
            if "quarantined" in state_flags:
                mask = state_flags["quarantined"].bool()
                mu = torch.where(mask, torch.zeros_like(mu), mu)
                nu = torch.where(mask, torch.ones_like(nu), nu) # High non-membership
            if "contradictory" in state_flags:
                mask = state_flags["contradictory"].bool()
                # High uncertainty -> mu and nu both small, pi high
                mu = torch.where(mask, torch.full_like(mu, 0.1), mu)
                nu = torch.where(mask, torch.full_like(nu, 0.1), nu)
            if "stale" in state_flags:
                mask = state_flags["stale"].bool()
                # Decay membership slightly
                mu = torch.where(mask, mu * 0.8, mu)

        violations_count = 0
        
        if self.fuzzy_family == "IFS":
            # Constraint: mu + nu <= 1
            sum_val = mu + nu
            violation_mask = sum_val > 1.0
            violations_count = int(violation_mask.sum().item())
            
            # Projection
            scale = torch.where(violation_mask, 1.0 / (sum_val + 1e-8), torch.ones_like(sum_val))
            mu_proj = mu * scale
            nu_proj = nu * scale
            pi = 1.0 - mu_proj - nu_proj
            
            mu, nu = mu_proj, nu_proj

        elif self.fuzzy_family == "PFS":
            # Constraint: mu^2 + nu^2 <= 1
            sum_sq = mu**2 + nu**2
            violation_mask = sum_sq > 1.0
            violations_count = int(violation_mask.sum().item())
            
            # Projection
            scale = torch.where(violation_mask, 1.0 / torch.sqrt(sum_sq + 1e-8), torch.ones_like(sum_sq))
            mu_proj = mu * scale
            nu_proj = nu * scale
            
            # Use clamp/max for numerical stability before sqrt
            pi = torch.sqrt(torch.clamp(1.0 - mu_proj**2 - nu_proj**2, min=0.0))
            
            mu, nu = mu_proj, nu_proj

        diagnostics = {
            "fuzzy_domain_violations": violations_count,
            "fuzzy_family": self.fuzzy_family,
        }
        
        if state_flags is not None and "stale" in state_flags:
            diagnostics["stale_edge_count"] = int(state_flags["stale"].sum().item())

        return mu, nu, pi, diagnostics
