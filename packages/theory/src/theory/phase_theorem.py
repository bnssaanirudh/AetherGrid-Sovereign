import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Tuple

class TopologyPreservingPhaseTheorem:
    """
    Formalizes the Topology-Preserving Phase Theorem implemented by the Quantum-Fuzzy Attention mechanism.
    
    Theorem Statement:
    Let a in C be a complex number representing a magnitude term, and theta in R be a phase angle.
    Then under the standard complex norm ||z|| = sqrt(Re(z)^2 + Im(z)^2), the phase transform
    T_theta(a) = a * exp(i * theta) preserves the magnitude: ||T_theta(a)|| = ||a||.
    """
    
    @staticmethod
    def domain() -> str:
        return "a in C (Complex Numbers), theta in R (Reals)"
        
    @staticmethod
    def complex_norm(z: np.ndarray) -> np.ndarray:
        return np.abs(z)
        
    @staticmethod
    def phase_transform(a: np.ndarray, theta: np.ndarray) -> np.ndarray:
        return a * np.exp(1j * theta)
        
    @classmethod
    def test_property_numerical(cls, num_samples: int = 10000, seed: int = 42) -> Tuple[bool, Dict[str, Any]]:
        np.random.seed(seed)
        
        # Random inputs
        real_parts = np.random.normal(0, 10, num_samples)
        imag_parts = np.random.normal(0, 10, num_samples)
        a_samples = real_parts + 1j * imag_parts
        theta_samples = np.random.uniform(-np.pi, np.pi, num_samples)
        
        # Adversarial cases (0, inf, NaN, very large, very small)
        adversarial_a = np.array([
            0 + 0j,
            1e-30 + 1e-30j,
            1e30 + 1e30j,
            np.inf + 0j, # Testing numerical stability
            np.nan + 1j * np.nan
        ], dtype=np.complex128)
        adversarial_theta = np.array([0, np.pi, -np.pi, 1e10, np.nan])
        
        # Combine
        a_all = np.concatenate([a_samples, adversarial_a])
        theta_all = np.concatenate([theta_samples, adversarial_theta])
        
        # Apply transform
        transformed = cls.phase_transform(a_all, theta_all)
        
        # Calculate norms
        norm_a = cls.complex_norm(a_all)
        norm_transformed = cls.complex_norm(transformed)
        
        # Check equality (mask out NaNs/Infs for the strict equality check)
        valid_mask = np.isfinite(norm_a) & np.isfinite(norm_transformed)
        
        max_error = np.max(np.abs(norm_a[valid_mask] - norm_transformed[valid_mask]))
        passed = max_error < 1e-10
        
        report = {
            "theorem": "Topology-Preserving Phase Theorem",
            "tested_function": "TopologyPreservingPhaseTheorem.test_property_numerical",
            "samples_tested": len(a_all),
            "max_numerical_error": float(max_error),
            "passed": bool(passed),
            "note": "This local operation guarantees magnitude preservation at the node embedding level, distinct from whole-network topology preservation or predictive robustness."
        }
        
        return passed, report

    @staticmethod
    def generate_latex_appendix() -> str:
        return r"""
\section{Appendix: Topology-Preserving Phase Theorem}

\subsection{Formal Statement}
Let $\mathcal{H}$ be a complex-valued embedding space where node representations reside. For any magnitude term $a \in \mathbb{C}$ and any phase angle $\theta \in \mathbb{R}$ induced by the quantum-fuzzy attention mechanism, we define the local phase transform as:
\begin{equation}
T_{\theta}(a) = a \cdot e^{i\theta}
\end{equation}

\textbf{Theorem 1 (Magnitude Preservation).} Under the standard complex norm $\|z\| = \sqrt{\text{Re}(z)^2 + \text{Im}(z)^2}$, the phase transform $T_{\theta}$ is an isometry with respect to the origin. That is, $\|T_{\theta}(a)\| = \|a\|$.

\begin{proof}
By definition of the complex exponential, $e^{i\theta} = \cos(\theta) + i\sin(\theta)$.
The norm of the exponential is:
\begin{equation}
\|e^{i\theta}\| = \sqrt{\cos^2(\theta) + \sin^2(\theta)} = 1
\end{equation}
Using the multiplicative property of the complex norm ($\|z_1 z_2\| = \|z_1\| \|z_2\|$):
\begin{equation}
\|T_{\theta}(a)\| = \|a \cdot e^{i\theta}\| = \|a\| \cdot \|e^{i\theta}\| = \|a\| \cdot 1 = \|a\|
\end{equation}
\end{proof}

\subsection{Operational Interpretation}
This theorem strictly proves that the local phase shift applied during temporal attention does not alter the structural magnitude of the node embedding. It is \textit{not} a proof of whole-network topology preservation under cascade dynamics, nor does it guarantee predictive robustness against adversarial perturbations in the input features.
"""

    @classmethod
    def export_artifacts(cls, out_dir: str = "artifacts/proofs"):
        path = Path(out_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        # LaTeX
        with open(path / "proof_appendix.tex", "w") as f:
            f.write(cls.generate_latex_appendix())
            
        # Numerical Report
        passed, report = cls.test_property_numerical()
        with open(path / "numerical_theorem_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        return passed
