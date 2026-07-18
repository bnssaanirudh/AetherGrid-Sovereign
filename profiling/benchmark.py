import time
import torch
from torch_geometric.data import HeteroData
import gc
import json

from core.hgt_model import AetherHGT

def create_medium_fixture(num_power=100, num_hospital=50, num_road=200, num_citizen=500):
    data = HeteroData()
    data["power"].x = torch.randn(num_power, 16)
    data["hospital"].x = torch.randn(num_hospital, 12)
    data["road"].x = torch.randn(num_road, 10)
    data["citizen"].x = torch.randn(num_citizen, 8)
    
    # Random edges
    data["power", "supplies", "hospital"].edge_index = torch.randint(0, min(num_power, num_hospital), (2, 300))
    data["power", "supplies", "hospital"].edge_attr = torch.rand(300, 4)
    
    data["power", "energizes", "road"].edge_index = torch.randint(0, min(num_power, num_road), (2, 800))
    data["power", "energizes", "road"].edge_attr = torch.rand(800, 4)
    
    return data

def benchmark_model(variant, data, num_runs=5):
    model = AetherHGT(hidden_dim=64, num_layers=2, num_heads=4, variant=variant)
    model.eval()
    
    # Warmup
    with torch.no_grad():
        model(data)
    
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        
    start_time = time.time()
    for _ in range(num_runs):
        with torch.no_grad():
            model(data)
    end_time = time.time()
    
    avg_latency = ((end_time - start_time) / num_runs) * 1000 # ms
    
    memory_mb = 0
    if torch.cuda.is_available():
        memory_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
        
    return {
        "latency_ms": round(avg_latency, 2),
        "peak_memory_mb": round(memory_mb, 2)
    }

if __name__ == "__main__":
    print("Generating fixture...")
    data = create_medium_fixture()
    
    variants = ["real_hgt", "cv_pfa_analytic", "cv_pfa_mlp"]
    results = {}
    
    print("Benchmarking...")
    for var in variants:
        print(f"Running {var}...")
        try:
            res = benchmark_model(var, data)
            results[var] = res
            print(f"  -> {res}")
        except Exception as e:
            print(f"  -> Failed: {e}")
            
    import os
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/prompt_03_handoff.json", "w") as f:
        json.dump({"benchmarks": results}, f, indent=2)
    
    print("Done. Results saved to artifacts/prompt_03_handoff.json.")
