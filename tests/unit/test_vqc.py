import torch
import pytest
import math
from core.phase_generator import VQCPhaseGenerator, MLPPhaseGenerator

def test_vqc_deterministic_output():
    vqc1 = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=2, num_qubits=4, circuit_depth=2, seed=42)
    vqc2 = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=2, num_qubits=4, circuit_depth=2, seed=42)
    
    # Ensure weights match for the test
    vqc2.vqc_weights.data.copy_(vqc1.vqc_weights.data)
    vqc2.input_proj.load_state_dict(vqc1.input_proj.state_dict())
    
    hesitation = torch.rand(5, 1)
    staleness = torch.rand(5, 1)
    edge_type = torch.rand(5, 4)
    src = torch.rand(5, 4)
    dst = torch.rand(5, 4)
    stress = torch.rand(5, 1)
    
    out1, _ = vqc1(hesitation, staleness, edge_type, src, dst, stress)
    out2, _ = vqc2(hesitation, staleness, edge_type, src, dst, stress)
    
    assert torch.allclose(out1, out2)

def test_vqc_finite_gradients():
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=2, num_qubits=4, circuit_depth=2, seed=42)
    
    hesitation = torch.rand(5, 1, requires_grad=True)
    staleness = torch.rand(5, 1)
    edge_type = torch.rand(5, 4)
    src = torch.rand(5, 4)
    dst = torch.rand(5, 4)
    stress = torch.rand(5, 1)
    
    out, _ = vqc(hesitation, staleness, edge_type, src, dst, stress)
    loss = out.sum()
    loss.backward()
    
    assert vqc.vqc_weights.grad is not None
    assert torch.isfinite(vqc.vqc_weights.grad).all()
    # Check nonzero gradient (at least one element should be non-zero for expressive inputs)
    assert torch.any(vqc.vqc_weights.grad != 0)
    assert hesitation.grad is not None

def test_vqc_fallback_behavior():
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=2, num_qubits=4, circuit_depth=2, seed=42)
    
    # Simulate a missing PennyLane or circuit execution error
    vqc.has_pennylane = False 
    
    hesitation = torch.rand(5, 1)
    staleness = torch.rand(5, 1)
    edge_type = torch.rand(5, 4)
    src = torch.rand(5, 4)
    dst = torch.rand(5, 4)
    stress = torch.rand(5, 1)
    
    out, diag = vqc(hesitation, staleness, edge_type, src, dst, stress)
    
    assert diag["vqc_fallback"] is True
    assert out.shape == (5, 2)

def test_vqc_phase_bounds():
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=2, num_qubits=4, circuit_depth=2, seed=42)
    
    hesitation = torch.rand(10, 1)
    staleness = torch.rand(10, 1)
    edge_type = torch.rand(10, 4)
    src = torch.rand(10, 4)
    dst = torch.rand(10, 4)
    stress = torch.rand(10, 1)
    
    out, diag = vqc(hesitation, staleness, edge_type, src, dst, stress)
    
    assert torch.all(out >= -math.pi) and torch.all(out <= math.pi)
    assert diag["phase_min"] >= -math.pi
    assert diag["phase_max"] <= math.pi

def test_vqc_serialization_roundtrip(tmp_path):
    """Save/load must reproduce output within float32 tolerance."""
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=1, num_qubits=4, circuit_depth=2, seed=42)
    
    hesitation = torch.rand(4, 1)
    staleness  = torch.rand(4, 1)
    edge_type  = torch.rand(4, 4)
    src        = torch.rand(4, 4)
    dst        = torch.rand(4, 4)
    stress     = torch.rand(4, 1)
    
    out_before, _ = vqc(hesitation, staleness, edge_type, src, dst, stress)
    
    ckpt = tmp_path / "vqc.pt"
    torch.save(vqc.state_dict(), ckpt)
    
    vqc2 = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=1, num_qubits=4, circuit_depth=2, seed=42)
    vqc2.load_state_dict(torch.load(ckpt))
    out_after, _ = vqc2(hesitation, staleness, edge_type, src, dst, stress)
    
    assert torch.allclose(out_before, out_after, atol=1e-5), \
        f"Mismatch after reload: max diff {(out_before - out_after).abs().max()}"

def test_vqc_extreme_inputs():
    """VQC should not crash or produce NaN on extreme (zero, one) fuzzy states."""
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=1, num_qubits=4, circuit_depth=2, seed=42)
    
    for val in [0.0, 1.0]:
        hesitation = torch.full((3, 1), val)
        staleness  = torch.full((3, 1), val)
        edge_type  = torch.zeros(3, 4) + val
        src        = torch.zeros(3, 4) + val
        dst        = torch.zeros(3, 4) + val
        stress     = torch.full((3, 1), val)
        
        out, diag = vqc(hesitation, staleness, edge_type, src, dst, stress)
        assert torch.isfinite(out).all(), f"NaN/Inf at extreme val={val}"

def test_vqc_circuit_config_validation():
    """out_dim > num_qubits must raise ValueError (we measure only first out_dim qubits)."""
    with pytest.raises(ValueError, match="out_dim"):
        VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=10, num_qubits=4,
                          circuit_depth=2, seed=42)

def test_vqc_no_external_hardware_dependency():
    """VQC must run without any external quantum hardware service (default.qubit is pure CPU)."""
    vqc = VQCPhaseGenerator(edge_embed_dim=4, node_dim=4, out_dim=1, num_qubits=4, circuit_depth=2, seed=42)
    assert vqc.backend == "default.qubit", "Default backend must be 'default.qubit' (software simulator)"
    
    hesitation = torch.rand(2, 1)
    out, diag = vqc(hesitation, torch.rand(2,1), torch.rand(2,4), torch.rand(2,4), torch.rand(2,4), torch.rand(2,1))
    assert not diag["vqc_fallback"], "Circuit should run without fallback on default.qubit"
