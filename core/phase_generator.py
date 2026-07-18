"""
phase_generator.py
------------------
Generates the complex phase (theta) for edge representations.
"""

from __future__ import annotations

import math
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Literal

import torch
import torch.nn as nn
from torch import Tensor

logger = logging.getLogger(__name__)

class PhaseGenerator(nn.Module, ABC):
    """
    Common interface for generating phase angles based on uncertainty and context.
    """
    @abstractmethod
    def forward(
        self,
        hesitation: Tensor,
        staleness: Tensor | None,
        edge_type_embedding: Tensor,
        source_state: Tensor,
        destination_state: Tensor,
        local_stress: Tensor | None,
    ) -> Tuple[Tensor, Dict[str, Any]]:
        pass

    def _wrap_phase(self, theta: Tensor) -> Tensor:
        """Wraps phase to [-pi, pi]"""
        return (theta + math.pi) % (2 * math.pi) - math.pi

    def _compute_diagnostics(self, theta: Tensor) -> Dict[str, Any]:
        """Compute basic phase distribution stats without raw inputs."""
        cos_mean = torch.cos(theta).mean().item()
        sin_mean = torch.sin(theta).mean().item()
        r = math.sqrt(cos_mean**2 + sin_mean**2)
        circ_var = 1.0 - r
        
        return {
            "phase_mean": theta.mean().item(),
            "phase_circ_var": circ_var,
            "phase_min": theta.min().item(),
            "phase_max": theta.max().item(),
        }

class AnalyticPhaseGenerator(PhaseGenerator):
    """
    Deterministic analytic phase for reference tests.
    """
    def __init__(self, out_dim: int = 1) -> None:
        super().__init__()
        self.out_dim = out_dim

    def forward(
        self, hesitation: Tensor, staleness: Tensor | None, edge_type_embedding: Tensor,
        source_state: Tensor, destination_state: Tensor, local_stress: Tensor | None,
    ) -> Tuple[Tensor, Dict[str, Any]]:
        embed_mean = edge_type_embedding.mean(dim=-1, keepdim=True)
        theta = math.pi * hesitation * torch.tanh(embed_mean)
        if self.out_dim > 1:
            theta = theta.expand(-1, self.out_dim)
        theta = self._wrap_phase(theta)
        return theta, self._compute_diagnostics(theta)

class MLPPhaseGenerator(PhaseGenerator):
    """
    Parameter-matched classical MLP phase generator.
    """
    def __init__(
        self,
        edge_embed_dim: int,
        node_dim: int,
        out_dim: int = 1,
        hidden_dim: int = 16,
        num_layers: int = 2
    ) -> None:
        super().__init__()
        self.out_dim = out_dim
        in_dim = 1 + 1 + edge_embed_dim + 2 * node_dim + 1
        
        layers = []
        layers.append(nn.Linear(in_dim, hidden_dim))
        layers.append(nn.GELU())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.GELU())
        layers.append(nn.Linear(hidden_dim, out_dim))
        
        self.mlp = nn.Sequential(*layers)

    def forward(
        self, hesitation: Tensor, staleness: Tensor | None, edge_type_embedding: Tensor,
        source_state: Tensor, destination_state: Tensor, local_stress: Tensor | None,
    ) -> Tuple[Tensor, Dict[str, Any]]:
        
        E = hesitation.size(0)
        device = hesitation.device
        
        if staleness is None: staleness = torch.zeros(E, 1, device=device)
        if local_stress is None: local_stress = torch.zeros(E, 1, device=device)
            
        x = torch.cat([hesitation, staleness, edge_type_embedding, source_state, destination_state, local_stress], dim=-1)
        theta = self.mlp(x) * math.pi
        theta = self._wrap_phase(theta)
        return theta, self._compute_diagnostics(theta)

class VQCPhaseGenerator(PhaseGenerator):
    """
    Real Variational Quantum Circuit (VQC) phase generator.
    Simulated backend with fallback to MLP on failure.
    """
    def __init__(
        self,
        edge_embed_dim: int,
        node_dim: int,
        out_dim: int = 4,
        num_qubits: int = 4,
        circuit_depth: int = 2,
        backend: str = "default.qubit",
        seed: int = 42
    ) -> None:
        super().__init__()
        if out_dim > num_qubits:
            raise ValueError(
                f"out_dim ({out_dim}) must not exceed num_qubits ({num_qubits}). "
                "The circuit measures the first out_dim qubits only."
            )
        self.out_dim = out_dim
        self.num_qubits = num_qubits
        self.circuit_depth = circuit_depth
        self.backend = backend
        self.seed = seed
        
        # Check pennylane dependency
        try:
            import pennylane as qml
            self.qml = qml
            self.has_pennylane = True
        except ImportError:
            self.has_pennylane = False
            logger.warning("PennyLane not installed. VQCPhaseGenerator will ALWAYS fallback to MLP.")
        
        in_dim = 1 + 1 + edge_embed_dim + 2 * node_dim + 1
        # Project inputs to angle parameters
        self.input_proj = nn.Linear(in_dim, num_qubits)
        
        # Parameterized weights for strongly entangling layers
        # Shape: (layers, qubits, 3)
        self.vqc_weights = nn.Parameter(torch.randn(circuit_depth, num_qubits, 3))
        
        # Fair control MLP (fallback)
        # Compute roughly matching parameter count
        vqc_params = (in_dim * num_qubits + num_qubits) + (circuit_depth * num_qubits * 3)
        # MLP hidden param count: in_dim * h + h + h*out + out
        h_matched = max(4, int(vqc_params / (in_dim + out_dim + 2)))
        self.fallback_mlp = MLPPhaseGenerator(
            edge_embed_dim=edge_embed_dim, 
            node_dim=node_dim, 
            out_dim=out_dim, 
            hidden_dim=h_matched, 
            num_layers=1
        )
        
        if self.has_pennylane:
            # We must recreate the device and qnode lazily to support serialization easily,
            # or define them dynamically in forward, but defining qnode here is standard.
            # We use a batch-compatible definition.
            dev = qml.device(backend, wires=num_qubits)
            
            @qml.qnode(dev, interface="torch")
            def _circuit(inputs, weights):
                qml.templates.AngleEmbedding(inputs, wires=range(num_qubits), rotation='Y')
                qml.templates.StronglyEntanglingLayers(weights, wires=range(num_qubits))
                # Measure expectation of Z for the first `out_dim` qubits
                return [qml.expval(qml.PauliZ(i)) for i in range(out_dim)]
                
            self.circuit = _circuit

    def _execute_vqc(self, x_proj: Tensor) -> Tensor:
        # PennyLane 0.17.x requires 1-D inputs for AngleEmbedding.
        # Iterate per sample to build the result; stack at the end.
        N = x_proj.size(0)
        rows = []
        for i in range(N):
            sample = x_proj[i]  # 1-D tensor [num_qubits]
            res = self.circuit(sample, self.vqc_weights)
            # QNode returns a list of 0-d tensors (one per qubit observable)
            if isinstance(res, (list, tuple)):
                res = torch.stack([r if r.dim() > 0 else r.unsqueeze(0) for r in res], dim=-1)  # [out_dim]
            else:
                res = res.flatten()
            rows.append(res)
        return torch.stack(rows, dim=0)   # [N, out_dim]

    def forward(
        self, hesitation: Tensor, staleness: Tensor | None, edge_type_embedding: Tensor,
        source_state: Tensor, destination_state: Tensor, local_stress: Tensor | None,
    ) -> Tuple[Tensor, Dict[str, Any]]:

        E = hesitation.size(0)
        device = hesitation.device

        if staleness is None: staleness = torch.zeros(E, 1, device=device)
        if local_stress is None: local_stress = torch.zeros(E, 1, device=device)

        x = torch.cat([hesitation, staleness, edge_type_embedding, source_state, destination_state, local_stress], dim=-1)

        fallback_occurred = False
        try:
            if not self.has_pennylane:
                raise RuntimeError("PennyLane missing")

            # Fix seed immediately before VQC evaluation for reproducibility.
            # This does NOT fix stochastic training noise; it ensures the
            # quantum simulator's internal random state is canonical on each call.
            torch.manual_seed(self.seed)

            x_proj = self.input_proj(x)  # [E, num_qubits]

            # Map expval [-1, 1] -> [-pi, pi]
            # PennyLane 0.17.x returns float64; cast to float32 for PyTorch compatibility.
            vqc_out = self._execute_vqc(x_proj).to(torch.float32)
            theta = vqc_out * math.pi
            theta = theta.to(device)

        except Exception as e:
            fallback_occurred = True
            logger.warning(f"VQC execution failed, falling back to MLP. Reason: {e}")
            theta, _ = self.fallback_mlp(
                hesitation, staleness, edge_type_embedding,
                source_state, destination_state, local_stress
            )

        theta = self._wrap_phase(theta)
        diag = self._compute_diagnostics(theta)
        diag["vqc_fallback"] = fallback_occurred
        return theta, diag
