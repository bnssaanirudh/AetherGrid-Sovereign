import math
import torch
import pytest

from core.fuzzy_state import FuzzyStateEncoder
from core.cv_pfa_attention import CVPFAAttention
from core.phase_generator import AnalyticPhaseGenerator

def test_pfs_and_ifs_domain_constraints():
    # Test strict adherence to domain boundaries
    encoder_ifs = FuzzyStateEncoder(in_features=2, fuzzy_family="IFS", mode="analytic")
    encoder_pfs = FuzzyStateEncoder(in_features=2, fuzzy_family="PFS", mode="analytic")
    
    # Random inputs that might exceed bounds
    inputs = torch.randn(100, 2) * 5
    
    mu_ifs, nu_ifs, pi_ifs, _ = encoder_ifs(inputs)
    assert torch.all(mu_ifs >= 0) and torch.all(mu_ifs <= 1)
    assert torch.all(nu_ifs >= 0) and torch.all(nu_ifs <= 1)
    # IFS Constraint: mu + nu <= 1
    assert torch.all((mu_ifs + nu_ifs) <= 1.0 + 1e-5)
    
    mu_pfs, nu_pfs, pi_pfs, _ = encoder_pfs(inputs)
    assert torch.all(mu_pfs >= 0) and torch.all(mu_pfs <= 1)
    assert torch.all(nu_pfs >= 0) and torch.all(nu_pfs <= 1)
    # PFS Constraint: mu^2 + nu^2 <= 1
    assert torch.all((mu_pfs**2 + nu_pfs**2) <= 1.0 + 1e-5)

def test_phase_norm_preservation():
    # Test that complex rotation z = rho * exp(i*theta) preserves magnitude
    mu = torch.rand(10, 1) * 0.5 + 0.1
    theta = torch.rand(10, 1) * 2 * math.pi - math.pi
    
    # Manual rotation
    z = torch.polar(mu, theta)
    r_z = torch.abs(z)
    
    assert torch.allclose(r_z, mu, atol=1e-5)

def test_maximal_hesitation_topology_preservation():
    # At maximal hesitation (pi=1, mu=0), topology channel should still be bounded > 0
    attn = CVPFAAttention(in_dim=16, num_heads=4, topology_min_bound=0.1)
    
    q = torch.randn(2, 4, 4)
    k = torch.randn(2, 4, 4)
    v = torch.randn(2, 4, 4)
    edge_index = torch.tensor([[0], [1]])
    
    # Maximal hesitation
    mu = torch.zeros(1, 1)
    nu = torch.zeros(1, 1)
    pi = torch.ones(1, 1)
    theta = torch.tensor([[math.pi]])
    
    agg, diag = attn(q, k, v, edge_index, mu, nu, pi, theta, 2)
    
    # topology_mag_mean should be at least topology_min_bound (0.1)
    assert diag["topology_mag_mean"] >= 0.1
    assert diag["confidence_mag_mean"] == 0.0

def test_finite_gradients_complex_ops():
    attn = CVPFAAttention(in_dim=16, num_heads=4, topology_min_bound=0.1)
    q = torch.randn(2, 4, 4, requires_grad=True)
    k = torch.randn(2, 4, 4, requires_grad=True)
    v = torch.randn(2, 4, 4, requires_grad=True)
    edge_index = torch.tensor([[0], [1]])
    mu = torch.rand(1, 1, requires_grad=True)
    nu = torch.rand(1, 1)
    pi = torch.rand(1, 1)
    theta = torch.rand(1, 1, requires_grad=True)
    
    agg, _ = attn(q, k, v, edge_index, mu, nu, pi, theta, 2)
    loss = agg.sum()
    loss.backward()
    
    assert q.grad is not None and torch.all(torch.isfinite(q.grad))
    assert k.grad is not None and torch.all(torch.isfinite(k.grad))
    assert v.grad is not None and torch.all(torch.isfinite(v.grad))
    assert mu.grad is not None and torch.all(torch.isfinite(mu.grad))
