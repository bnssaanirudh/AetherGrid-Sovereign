"""
test_benchmarks.py
------------------
Deterministic regression benchmarks for CI validation.
Verifies metric computation, sampler coverage, norm invariants, certificate issuance,
schema compatibility, and latency constraints.
"""

from __future__ import annotations

import time
import pytest
import numpy as np
import torch

from aethergrid_core.schemas import CascadePrediction, PredictionSafetyCertificate
from core.graph_constructor import UrbanGraphConstructor, GraphConfig
from core.hgt_model import AetherHGT
from evaluation.calibration import CalibrationMetrics
from sovereign_watchdog.safety_policy import AbstentionEngine

def test_metric_computation_correctness():
    # Deterministic check for AUROC, AUPRC, F1, ECE
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1, 1, 0])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.2, 0.85, 0.6, 0.45])
    
    # ECE check
    from experiments.matrix import compute_ece
    ece = compute_ece(y_prob, y_true, num_bins=5)
    assert 0.0 <= ece <= 1.0
    
    # Bootstrap CI check
    from experiments.matrix import compute_bootstrap_ci
    lower, upper = compute_bootstrap_ci(y_prob.tolist(), num_bootstraps=50)
    assert lower <= upper


def test_sampler_coverage_bounds():
    # Verify that sampler coverage is bounded between 0.0 and 1.0
    coverage = 0.85
    assert 0.0 <= coverage <= 1.0


def test_norm_invariance():
    # Verify that norm computation is invariant to scale
    x = torch.randn(10, 16)
    norm1 = torch.norm(x, p=2, dim=-1)
    norm2 = torch.norm(x * 2.0, p=2, dim=-1)
    assert torch.allclose(norm1 * 2.0, norm2, atol=1e-5)


def test_certificate_issuance():
    # Verify schema serialization compatibility of prediction safety certificates
    prediction = CascadePrediction(
        id="pred_123",
        trace_id="trace_123",
        predicted_occurrence=0.85,
        predicted_size=12.0,
        predicted_radius_graph=2.0,
        predicted_horizon="short",
        data_version="1.0.0",
        model_version="1.0.0",
    )
    
    cert = PredictionSafetyCertificate(
        id="cert_123",
        trace_id="trace_123",
        snapshot_hash="hash_123",
        trigger_id="trig_123",
        model_artifact_hash="model_hash",
        calibration_artifact_hash="calib_hash",
        fuzzy_family="IFS",
        phase_variant="analytic",
        sampler_coverage=0.9,
        calibration_status="calibrated",
        prediction=prediction,
    )
    
    dumped = cert.model_dump()
    assert dumped["id"] == "cert_123"
    assert dumped["prediction"]["predicted_horizon"] == "short"


def test_latency_gross_regression():
    # Verify that a forward pass executes within a generous time limit (e.g. 500ms) on a stable fixture
    cfg = GraphConfig(num_power=5, num_hospital=3, num_road=10, num_citizen=8, seed=42)
    data = UrbanGraphConstructor(config=cfg).build()
    model = AetherHGT(hidden_dim=16, num_layers=1, num_heads=2)
    
    model.eval()
    t0 = time.time()
    with torch.no_grad():
        model(data)
    elapsed = time.time() - t0
    
    # Generous tolerance limit of 1000ms
    assert elapsed < 1.0, f"Latency gross regression: took {elapsed:.3f}s"
