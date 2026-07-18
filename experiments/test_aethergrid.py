"""
test_aethergrid.py
------------------
Unit tests for AetherGrid-Sovereign core components.
Run with: pytest experiments/test_aethergrid.py -v
"""

import pytest
import torch
import numpy as np


# ---------------------------------------------------------------------------
# Graph Constructor
# ---------------------------------------------------------------------------

def test_graph_construction():
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from core.schema import NODE_TYPES
    cfg = GraphConfig(num_power=5, num_hospital=3, num_road=10, num_citizen=8)
    constructor = UrbanGraphConstructor(config=cfg)
    data = constructor.build()
    for nt in NODE_TYPES:
        assert hasattr(data[nt], "x"), f"Missing x for {nt}"
        assert not torch.isnan(data[nt].x).any(), f"NaN in {nt} features"


# ---------------------------------------------------------------------------
# Fuzzy Attention
# ---------------------------------------------------------------------------

def test_ifs_constraint_satisfied():
    """mu + nu must be <= 1 for all edges."""
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from core.schema import EDGE_TYPES
    cfg = GraphConfig(num_power=5, num_hospital=3, num_road=10, num_citizen=8)
    data = UrbanGraphConstructor(config=cfg).build()
    for src, rel, dst in EDGE_TYPES:
        store = data[src, rel, dst]
        if hasattr(store, "edge_attr"):
            ea = store.edge_attr
            mu, nu = ea[:, 0], ea[:, 1]
            assert (mu + nu <= 1.0 + 1e-4).all(), f"IFS violated in {src}__{rel}__{dst}"


def test_fuzzy_attention_forward():
    from core.fuzzy_attention import IntuitionisticFuzzyAttention
    attn = IntuitionisticFuzzyAttention(in_dim=16, num_heads=2)
    N, E = 8, 12
    query = torch.randn(N, 16)
    key   = torch.randn(N, 16)
    edge_index = torch.randint(0, N, (2, E))
    edge_attr  = torch.rand(E, 4)
    # Ensure IFS constraint
    edge_attr[:, 1] = edge_attr[:, 1] * (1.0 - edge_attr[:, 0])
    weights, (mu, nu, pi) = attn(query, key, edge_index, edge_attr)
    assert weights.shape == (E, 2)
    assert (mu + nu <= 1.0 + 1e-5).all(), "IFS constraint violated in attention"
    assert (pi >= -1e-4).all(), "Hesitation margin went negative"


# ---------------------------------------------------------------------------
# QF Fusion
# ---------------------------------------------------------------------------

def test_qf_fusion_output_shape():
    from core.quantum_fuzzy_fusion import QuantumFuzzyFusion
    block = QuantumFuzzyFusion(src_dim=16, dst_dim=16, out_dim=16, num_heads=2)
    N_src, N_dst, E = 10, 8, 15
    x_src = torch.randn(N_src, 16)
    x_dst = torch.randn(N_dst, 16)
    ei    = torch.stack([
        torch.randint(0, N_src, (E,)),
        torch.randint(0, N_dst, (E,))
    ])
    ea = torch.rand(E, 4)
    ea[:, 1] *= (1.0 - ea[:, 0])
    out, diag = block(x_src, x_dst, ei, ea)
    assert out.shape == (N_dst, 16)
    assert "mu" in diag and "pi" in diag


# ---------------------------------------------------------------------------
# Full AetherHGT
# ---------------------------------------------------------------------------

def test_aether_hgt_forward():
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from core.hgt_model import AetherHGT
    from core.schema import NODE_TYPES
    cfg   = GraphConfig(num_power=4, num_hospital=3, num_road=8, num_citizen=5)
    data  = UrbanGraphConstructor(config=cfg).build()
    model = AetherHGT(hidden_dim=16, num_layers=1, num_heads=2)
    model.eval()
    with torch.no_grad():
        preds, diags = model(data, return_attention=True)
    for nt in NODE_TYPES:
        assert preds[nt].shape[1] == 1
        assert (preds[nt] >= 0).all() and (preds[nt] <= 1).all()


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

def test_watchdog_passes_clean_graph():
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from watchdog.sovereign_watchdog import SovereignWatchdog
    cfg  = GraphConfig(num_power=4, num_hospital=3, num_road=8, num_citizen=5)
    data = UrbanGraphConstructor(config=cfg).build()
    wd   = SovereignWatchdog(strict=True)
    report = wd.validate(data, epoch=1)
    assert report.overall_passed, f"Watchdog failed on clean graph: {report.fatal_messages}"


def test_watchdog_fails_nan_injection():
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from watchdog.sovereign_watchdog import SovereignWatchdog, WatchdogError
    cfg  = GraphConfig(num_power=4, num_hospital=3, num_road=8, num_citizen=5)
    data = UrbanGraphConstructor(config=cfg).build()
    # Inject NaN
    data["power"].x[0, 0] = float("nan")
    wd = SovereignWatchdog(strict=True)
    with pytest.raises(WatchdogError):
        wd.validate(data, epoch=1)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def test_build_ifs_edge_attributes():
    from data.preprocessing import build_ifs_edge_attributes
    edge_index = torch.tensor([[0, 1], [1, 0]])
    base_weight = torch.tensor([0.6, 0.4])
    damage_proxy = torch.tensor([0.2, 0.8])
    temporal_decay = torch.tensor([0.9, 0.7])
    out = build_ifs_edge_attributes(edge_index, base_weight, damage_proxy, temporal_decay)
    assert out.shape == (2, 4)
    mu, nu = out[:, 0], out[:, 1]
    assert (mu + nu <= 1.0 + 1e-5).all()


def test_fuse_temporal_weather():
    from data.preprocessing import fuse_temporal_weather
    base = np.random.rand(5, 6).astype(np.float32)
    weather = np.random.rand(10, 4).astype(np.float32)
    out = fuse_temporal_weather(base, weather)
    assert out.shape[0] == 5
    assert out.dtype == np.float32


# ---------------------------------------------------------------------------
# NAS
# ---------------------------------------------------------------------------

def test_nas_controller_runs():
    from core.graph_constructor import UrbanGraphConstructor, GraphConfig
    from optimization.nas_search import NASController
    from optimization.q_avoa import QAVOAConfig
    cfg = GraphConfig(num_power=4, num_hospital=3, num_road=8, num_citizen=5)
    data = UrbanGraphConstructor(config=cfg).build()
    avoa_cfg = QAVOAConfig(population_size=4, max_iter=2)
    nas = NASController(graph_data=data, proxy_epochs=1, device="cpu", avoa_config=avoa_cfg)
    best = nas.run()
    assert "hidden_dim" in best
    assert "num_layers" in best


# ---------------------------------------------------------------------------
# Smoke training
# ---------------------------------------------------------------------------

def test_train_smoke(tmp_path):
    import yaml
    from experiments.train import train
    cfg_path = tmp_path / "config.yaml"

    cfg = {
        "model": {"hidden_dim": 16, "num_layers": 1, "num_heads": 2, "dropout": 0.1, "quantize": False},
        "training": {
            "epochs": 1,
            "learning_rate": 0.001,
            "weight_decay": 1.0e-5,
            "batch_size": 1,
            "grad_clip": 1.0,
            "patience": 1,
            "device": "cpu",
            "seed": 123,
            "val_ratio": 0.2,
            "output_dir": str(tmp_path / "runs"),
            "labels": {"mode": "synthetic", "path": ""},
        },
        "nas": {"enabled": False, "population_size": 4, "max_iter": 2, "proxy_epochs": 1, "chaotic_map": "tent"},
        "graph": {
            "num_power": 4,
            "num_hospital": 3,
            "num_road": 8,
            "num_citizen": 5,
            "edge_density": 0.2,
            "normalize_features": True,
            "seed": 123,
            "use_toy_data": True,
        },
        "watchdog": {"strict": True, "run_every_n_epochs": 1},
        "logging": {"level": "INFO", "log_file": str(tmp_path / "runs" / "train.log")},
        "datasets": {"toy_graph_path": "./data/toy_graph.json"},
    }

    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    train(str(cfg_path))


# ---------------------------------------------------------------------------
# Chaotic Maps
# ---------------------------------------------------------------------------

def test_chaotic_maps_bounds():
    from optimization.chaotic_maps import generate_chaotic_sequence
    for map_type in ["logistic", "tent", "sine", "chebyshev"]:
        seq = generate_chaotic_sequence(200, map_type=map_type)
        assert seq.min() >= 0.0, f"{map_type} produced values < 0"
        assert seq.max() <= 1.0, f"{map_type} produced values > 1"


def test_chaotic_population_init_shape():
    from optimization.chaotic_maps import chaotic_population_init
    lb = np.zeros(6)
    ub = np.ones(6)
    pop = chaotic_population_init(20, 6, lb, ub)
    assert pop.shape == (20, 6)
    assert (pop >= 0).all() and (pop <= 1).all()


# ---------------------------------------------------------------------------
# Q-AVOA (surrogate fitness)
# ---------------------------------------------------------------------------

def test_q_avoa_runs():
    from optimization.q_avoa import QuantumVultureOptimizer, QAVOAConfig
    cfg = QAVOAConfig(population_size=5, max_iter=5)
    opt = QuantumVultureOptimizer(config=cfg)
    result = opt.search()
    assert "hidden_dim" in result
    assert "num_layers" in result
    assert result["hidden_dim"] in [32, 64, 128, 256]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
