"""
test_migration.py
------------------
Integrity validation tests for the target monorepo architecture and domain contracts.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
import pytest
import numpy as np
import torch
from torch_geometric.data import HeteroData

# Monorepo imports
from aethergrid_core import NodeRecord, FuzzyState, resolve_node_type
from evaluation import evaluate_metrics, temporal_split
from sovereign_watchdog import SovereignWatchdog, WatchdogError
from training import save_checkpoint, load_checkpoint


# ---------------------------------------------------------------------------
# 1. Schema serialization & validation
# ---------------------------------------------------------------------------

def test_schema_serialization():
    rec = NodeRecord(
        id="node_123",
        node_type="road_segment",
        is_synthetic=True,
        source="unit_test",
        crs="EPSG:4326",
        coordinates=(12.34, 56.78),
        attributes={"speed_limit": 50},
        validation_status="verified",
    )
    data = rec.model_dump()
    assert data["id"] == "node_123"
    assert data["node_type"] == "road_segment"
    assert data["is_synthetic"] is True

    # Check version resolution
    with pytest.raises(ValueError):
        resolve_node_type("invalid_type_name")


# ---------------------------------------------------------------------------
# 2. Fuzzy-family constraints
# ---------------------------------------------------------------------------

def test_fuzzy_family_constraints():
    # Valid IFS
    fs_ifs_val = FuzzyState(membership=0.4, non_membership=0.5, fuzzy_family="IFS")
    assert fs_ifs_val.hesitation == pytest.approx(0.1)

    # Invalid IFS
    with pytest.raises(ValueError, match="IFS violation"):
        FuzzyState(membership=0.7, non_membership=0.4, fuzzy_family="IFS")

    # Valid PFS
    fs_pfs_val = FuzzyState(membership=0.8, non_membership=0.5, fuzzy_family="PFS")
    # 0.8^2 + 0.5^2 = 0.64 + 0.25 = 0.89 <= 1
    assert fs_pfs_val.hesitation == pytest.approx((1.0 - 0.89)**0.5)

    # Invalid PFS
    with pytest.raises(ValueError, match="PFS violation"):
        FuzzyState(membership=0.9, non_membership=0.5, fuzzy_family="PFS")


# ---------------------------------------------------------------------------
# 3. Invalid metric/label combinations fail loudly
# ---------------------------------------------------------------------------

def test_invalid_metric_label_combinations():
    y_true_continuous = np.array([0.3, 0.45, 0.8])
    y_score = np.array([0.2, 0.5, 0.75])

    # continuous labels on binary occurrence must raise ValueError
    with pytest.raises(ValueError, match="continuous/non-binary value"):
        evaluate_metrics(y_true_continuous, y_score, task_type="binary_occurrence")

    # Binary occurrence on valid binary labels should pass
    y_true_binary = np.array([0.0, 1.0, 0.0])
    metrics = evaluate_metrics(y_true_binary, y_score, task_type="binary_occurrence")
    assert "f1" in metrics
    assert "auc" in metrics


# ---------------------------------------------------------------------------
# 4. Temporal split leakage detection
# ---------------------------------------------------------------------------

def test_temporal_split_leakage():
    snapshots = [
        {"id": "s1", "timestamp": "2026-01-01T12:00:00"},
        {"id": "s2", "timestamp": "2026-01-02T12:00:00"},
        {"id": "s3", "timestamp": "2026-01-03T12:00:00"},
    ]

    # Clean split
    train, val = temporal_split(snapshots, train_ratio=0.6)
    assert len(train) == 1
    assert len(val) == 2
    assert train[0]["id"] == "s1"

    # Leakage injection
    snapshots_leaked = [
        {"id": "s1", "timestamp": "2026-01-03T12:00:00"},
        {"id": "s2", "timestamp": "2026-01-01T12:00:00"},
    ]
    # This should sort them: s2 (train), s1 (val)
    train_l, val_l = temporal_split(snapshots_leaked, train_ratio=0.5)
    # Train = s2 (Jan 1), Val = s1 (Jan 3) -> no leakage.
    assert train_l[0]["id"] == "s2"
    assert val_l[0]["id"] == "s1"


# ---------------------------------------------------------------------------
# 5. Checkpoint manifest completeness
# ---------------------------------------------------------------------------

def test_checkpoint_completeness():
    model = torch.nn.Linear(10, 2)
    with tempfile.TemporaryDirectory() as tmpdir:
        chk_path = os.path.join(tmpdir, "checkpoint.pt")
        save_checkpoint(
            path=chk_path,
            model=model,
            config_hash="conf123",
            data_manifest_hash="data123",
            source_commit="commit123",
            task_schema={"task_type": "regression_size"},
            epoch=1,
        )

        # Load back compatibility check
        loaded = load_checkpoint(chk_path, model)
        assert loaded["epoch"] == 1
        assert loaded["manifest"]["model_class"] == "Linear"
        assert loaded["manifest"]["config_hash"] == "conf123"

        # Check model type mismatch failure
        mismatched_model = torch.nn.Conv2d(3, 6, 3)
        with pytest.raises(ValueError, match="Model class mismatch"):
            load_checkpoint(chk_path, mismatched_model)


# ---------------------------------------------------------------------------
# 6. Production profile synthetic fallback guard
# ---------------------------------------------------------------------------

def test_production_profile_guard():
    # Build a simple mock graph
    data = HeteroData()
    data["power"].x = torch.randn(2, 16)
    data["power"].num_nodes = 2
    data["hospital"].x = torch.randn(2, 12)
    data["hospital"].num_nodes = 2
    data["road"].x = torch.randn(2, 10)
    data["road"].num_nodes = 2
    data["citizen"].x = torch.randn(2, 8)
    data["citizen"].num_nodes = 2

    # Add minimum connectivity edge
    data["power", "supplies", "hospital"].edge_index = torch.tensor([[0], [0]], dtype=torch.long)
    data["power", "supplies", "hospital"].edge_attr = torch.tensor([[0.4, 0.5, 0.8, 0.2]], dtype=torch.float32)

    # Set as synthetic graph
    data.is_synthetic = True
    data.allow_demo = False

    # Validation in research profile should pass fallback check
    wd_research = SovereignWatchdog(strict=True, profile="research")
    report = wd_research.validate(data, epoch=1)
    assert report.overall_passed is True

    # Validation in production profile must raise WatchdogError on synthetic fallback
    wd_production = SovereignWatchdog(strict=True, profile="production")
    with pytest.raises(WatchdogError, match="Production profile active but synthetic fallback detected"):
        wd_production.validate(data, epoch=1)
