"""
nas_search.py
-------------
Neural Architecture Search wrapper that combines Q-AVOA with
a fast proxy fitness evaluator for AetherHGT hyperparameter selection.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional

import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData

from .q_avoa import QuantumVultureOptimizer, QAVOAConfig
from models import AetherHGT

logger = logging.getLogger(__name__)

# Legacy node types for NAS runs
NODE_TYPES = ["power", "hospital", "road", "citizen"]


class NASController:
    def __init__(
        self,
        graph_data: HeteroData,
        proxy_epochs: int = 3,
        device: str = "cpu",
        avoa_config: Optional[QAVOAConfig] = None,
    ) -> None:
        self.device       = torch.device(device)
        self.data         = graph_data.to(self.device)
        self.proxy_epochs = proxy_epochs
        self._avoa_config = avoa_config or QAVOAConfig(
            population_size=10, max_iter=20
        )
        self._labels = {
            nt: labels.to(self.device)
            for nt, labels in self._make_labels().items()
        }

    def run(self) -> Dict:
        logger.info("Starting NAS with Q-AVOA (proxy_epochs=%d)", self.proxy_epochs)
        t0 = time.time()

        optimizer = QuantumVultureOptimizer(
            fitness_fn=self._proxy_fitness,
            config=self._avoa_config,
        )
        best_arch = optimizer.search()

        logger.info(
            "NAS complete in %.1fs | best_arch=%s", time.time() - t0, best_arch
        )
        return best_arch

    def _proxy_fitness(self, hp: Dict) -> float:
        model = AetherHGT(
            hidden_dim=hp["hidden_dim"],
            num_layers=hp["num_layers"],
            num_heads=hp["num_heads"],
            dropout=hp["dropout"],
        ).to(self.device)

        opt = torch.optim.Adam(model.parameters(), lr=hp["lr"])
        data = self.data

        model.train()
        total_loss = 0.0
        for _ in range(self.proxy_epochs):
            opt.zero_grad()
            preds, _ = model(data)
            loss = sum(
                F.binary_cross_entropy(
                    preds[nt].squeeze(-1),
                    self._labels[nt],
                )
                for nt in NODE_TYPES
                if nt in preds
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total_loss += loss.item()

        return total_loss / self.proxy_epochs

    def _make_labels(self) -> Dict[str, torch.Tensor]:
        labels = {}
        for nt in NODE_TYPES:
            n = self.data[nt].num_nodes
            labels[nt] = torch.full((n,), 0.3)
        return labels
