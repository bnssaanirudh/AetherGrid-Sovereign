"""
benchmark_vqc.py
----------------
Measure VQC latency and memory for 4-qubit and 6-qubit circuits
against a parameter-matched MLP, on a small batch.
"""
import json
import os
import time
import torch
from core.phase_generator import VQCPhaseGenerator

def measure(gen, hesitation, staleness, edge_type, src, dst, stress, warmup=2, reps=5):
    # Warmup
    for _ in range(warmup):
        gen(hesitation, staleness, edge_type, src, dst, stress)
    
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    t0 = time.perf_counter()
    for _ in range(reps):
        gen(hesitation, staleness, edge_type, src, dst, stress)
    elapsed = (time.perf_counter() - t0) / reps * 1000  # ms per call
    
    peak_mb = (torch.cuda.max_memory_allocated() / 1e6) if torch.cuda.is_available() else 0
    return round(elapsed, 2), round(peak_mb, 2)

def run():
    E = 5  # small batch for CI
    edge_embed_dim = 4
    node_dim = 4
    
    torch.manual_seed(42)
    hesitation = torch.rand(E, 1)
    staleness  = torch.rand(E, 1)
    edge_type  = torch.rand(E, edge_embed_dim)
    src        = torch.rand(E, node_dim)
    dst        = torch.rand(E, node_dim)
    stress     = torch.rand(E, 1)
    
    results = {}
    
    for n_q in [4, 6]:
        for depth in [2]:
            label = f"vqc_{n_q}q_d{depth}"
            gen = VQCPhaseGenerator(edge_embed_dim, node_dim, out_dim=1, num_qubits=n_q,
                                    circuit_depth=depth, seed=42)
            gen.eval()
            lat, mem = measure(gen, hesitation, staleness, edge_type, src, dst, stress)
            n_params = sum(p.numel() for p in gen.parameters() if p.requires_grad)
            results[label] = {"latency_ms": lat, "peak_memory_mb": mem, "n_params": n_params,
                              "num_qubits": n_q, "circuit_depth": depth}
            print(f"  {label}: {lat} ms, {mem} MB, {n_params} params")
    
    # MLP matched to 4q
    mlp = VQCPhaseGenerator(edge_embed_dim, node_dim, out_dim=1, num_qubits=4, circuit_depth=2, seed=42).fallback_mlp
    mlp.eval()
    lat, mem = measure(mlp, hesitation, staleness, edge_type, src, dst, stress)
    n_params = sum(p.numel() for p in mlp.parameters() if p.requires_grad)
    results["matched_mlp_4q"] = {"latency_ms": lat, "peak_memory_mb": mem, "n_params": n_params}
    print(f"  matched_mlp_4q: {lat} ms, {mem} MB, {n_params} params")
    
    os.makedirs("artifacts", exist_ok=True)
    handoff_path = "artifacts/prompt_04_handoff.json"
    if os.path.exists(handoff_path):
        with open(handoff_path, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data["vqc_benchmarks"] = results
    
    with open(handoff_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\nBenchmarks saved to {handoff_path}")

if __name__ == "__main__":
    run()
