# AetherHGT: Complex-Valued Pythagorean Fuzzy Attention (CV-PFA)

## Overview
This document mathematically specifies the integration of strict fuzzy sets with complex-valued representations inside the Heterogeneous Graph Transformer (AetherHGT). It explains how uncertain (hesitant) topologies are explicitly preserved rather than erased.

## 1. Strict Fuzzy Semantics
Instead of arbitrary heuristics, edge reliability is mapped into formally defined domains using the `FuzzyStateEncoder`:

### Intuitionistic Fuzzy Set (IFS)
Let $\mu$ be membership (reliability), $\nu$ be non-membership (failure confidence), and $\pi$ be hesitation.
$$ \mu, \nu \in [0, 1] $$
$$ \mu + \nu \le 1 $$
$$ \pi = 1 - \mu - \nu $$

### Pythagorean Fuzzy Set (PFS)
$$ \mu, \nu \in [0, 1] $$
$$ \mu^2 + \nu^2 \le 1 $$
$$ \pi = \sqrt{\max(0, 1 - \mu^2 - \nu^2)} $$

Edges exceeding bounds are numerically projected onto the valid hypersurface rather than silently clipped, generating diagnostic alerts.

## 2. Native Complex Phase Encoding
We represent the graph's messages in the complex plane $\mathbb{C}$. 
A fundamental invariant of our CV-PFA is **magnitude preservation under rotation**: for a complex number $z = \rho e^{i\theta}$, multiplying by a unitary phase $e^{i\phi}$ strictly preserves the magnitude $|ze^{i\phi}| = \rho$. 

The previous heuristic multiplied messages by an entropy penalty factor $(1 - \pi)$. As hesitation $\pi \to 1$, the edge magnitude was scaled to $0$, explicitly erasing the topology of uncertain edges.

### Topology vs. Confidence Channels
To prevent topological erasure, we explicitly split the attention into two complex channels before aggregation:

**1. Topology Channel:** 
Represents the structural presence of the edge. The magnitude $r_{top}$ is bounded below by a strictly positive threshold $\epsilon$. 
$$ z_{top} = \max(\mu, \epsilon) \cdot e^{i \theta} $$
Here, $\theta = \text{PhaseGenerator}(\pi, ...)$ is the uncertainty-conditioned phase. Even if an edge is entirely uncertain ($\mu \to 0, \pi \to 1$), it contributes a structural phase shift with magnitude $\epsilon$, preserving network connectivity gradients.

**2. Evidence-Confidence Channel:**
Represents the absolute trust in the edge's signal.
$$ z_{conf} = \mu \cdot e^{i \cdot 0} $$
This channel attenuates towards $0$ for unreliable edges, ensuring noise is gated out of the high-confidence readout paths.

### Complex-Valued Fusion
The base Real-valued similarity score $S_{base} = \frac{Q K^T}{\sqrt{d}}$ is modulated by both channels:
$$ Z_{fused} = S_{base} \cdot (z_{top} + z_{conf}) $$

The attention weights are derived from the magnitude $|Z_{fused}|$, while the values $V$ are rotated by the unit phase of $Z_{fused}$:
$$ \alpha = \text{softmax}_{dst}(|Z_{fused}|) $$
$$ V_{weighted} = V \cdot \alpha \cdot \frac{Z_{fused}}{|Z_{fused}|} $$

The readout is aggregated by taking the real part of the complex message path, ensuring a stable $\mathbb{C} \to \mathbb{R}$ transition for the downstream node features.

## 3. Claim Alignment
By using native PyTorch `torch.complex64` types, this implementation precisely guarantees magnitude bounds and rotational invariance. The topological presence of a sensor is structurally maintained in the gradient graph irrespective of its temporary signal reliability.

---

## 4. VQC Phase Generator

> **Claim discipline**: This is a simulated, narrow VQC phase generator running on PennyLane's `default.qubit` software simulator. It is **not** a quantum computer, does **not** demonstrate quantum advantage, is **not** certified for quantum hardware, and is **not** hardware-ready. All results come from classical state-vector simulation.

### 4.1 Purpose

The `VQCPhaseGenerator` replaces the analytic or MLP phase calculation with a parameterized quantum circuit whose expectation values are mapped to phase angles $\theta \in [-\pi, \pi]$. This is a narrow substitution: the rest of the CV-PFA pipeline remains classical.

### 4.2 Encoding Strategy

Inputs fed to the circuit are a linear projection of:
- `hesitation` ($\pi_{PFS}$)
- `staleness` (time-decay factor)
- `edge_type_embedding` (16-dim learned embedding)
- `source_state` / `destination_state` (node context)
- `local_stress` (congestion indicator)

The combined vector of size $1+1+16+D_n+D_n+1$ is projected by a learned `nn.Linear` down to `num_qubits` angle parameters before encoding.

### 4.3 Circuit Structure (4 qubits, depth 2)

```
q0: ─RY(a0)─┤ StronglyEntangling ├─┤ StronglyEntangling ├─⟨Z⟩
q1: ─RY(a1)─┤      Layer 1        ├─┤      Layer 2        ├─⟨Z⟩
q2: ─RY(a2)─┤                     ├─┤                     ├─⟨Z⟩
q3: ─RY(a3)─┤ (CNOT ring + RZ/RY)├─┤ (CNOT ring + RZ/RY)├─⟨Z⟩
```

- **Encoding**: `qml.templates.AngleEmbedding` with Y-rotation.
- **Entangling layer**: `qml.templates.StronglyEntanglingLayers`, which applies trainable Rot gates and a CNOT entangling pattern per layer.
- **Measurement**: PauliZ expectation for each qubit, yielding values in $[-1, 1]$, then scaled by $\pi$.

### 4.4 Simulation Limitations

- State-vector simulation scales as $O(2^n)$; keep `num_qubits ≤ 8` for CI.
- No shot noise in analytic mode.
- Noise experiments use `default.mixed` simulator with depolarizing channels, not real hardware noise.
- Per-sample iteration (no batching) due to PennyLane 0.17.x API constraints.

### 4.5 Matched Ablation Protocol

For fair comparison, `fallback_mlp` inside `VQCPhaseGenerator` is sized to approximately match the VQC trainable parameter count:
$$N_{\text{VQC params}} = (d_{\text{in}} \times n_q + n_q) + (L \times n_q \times 3)$$
The hidden dimension of the MLP is computed as $h = \max(4, \lfloor N_{\text{VQC params}} / (d_{\text{in}} + d_{\text{out}} + 2) \rfloor)$.

Both receive identical inputs and are trained with identical optimizers and epochs in the expressivity experiment.

### 4.6 Fallback Behavior

If the circuit execution raises any exception (including missing PennyLane, device failure, or shape mismatch), the VQC transparently falls back to the `fallback_mlp` with an explicit warning log entry and a `vqc_fallback: true` field in the diagnostics dict. This fallback is **never silent**.
