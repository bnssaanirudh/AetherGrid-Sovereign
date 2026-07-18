import json
import os
import torch
from torch import nn, optim
from core.phase_generator import VQCPhaseGenerator, MLPPhaseGenerator

def target_function(x):
    # x is [E, in_dim]
    # We create a nonlinear periodic target based on the sum of inputs
    s = x.sum(dim=-1, keepdim=True)
    return (torch.sin(2 * s) + torch.cos(s**2)) * 0.5 * 3.1415 # mapped roughly to [-pi, pi]

def run_expressivity_experiment():
    torch.manual_seed(42)
    
    # 1. Setup Data
    E = 200
    edge_embed_dim = 4
    node_dim = 4
    in_dim = 1 + 1 + edge_embed_dim + 2 * node_dim + 1
    
    # Synthetic inputs
    hesitation = torch.rand(E, 1)
    staleness = torch.rand(E, 1)
    edge_type = torch.rand(E, edge_embed_dim)
    src = torch.rand(E, node_dim)
    dst = torch.rand(E, node_dim)
    stress = torch.rand(E, 1)
    
    x_full = torch.cat([hesitation, staleness, edge_type, src, dst, stress], dim=-1)
    y_target = target_function(x_full).squeeze() # [E]
    
    # We train to predict a single phase out_dim=1
    vqc = VQCPhaseGenerator(edge_embed_dim, node_dim, out_dim=1, num_qubits=4, circuit_depth=2, seed=42)
    mlp = vqc.fallback_mlp # already parameter matched for out_dim=1, actually out_dim is from vqc init.
    
    vqc_opt = optim.Adam(vqc.parameters(), lr=0.1)
    mlp_opt = optim.Adam(mlp.parameters(), lr=0.1)
    criterion = nn.MSELoss()
    
    epochs = 20
    
    def train_loop(model, opt, name):
        model.train()
        losses = []
        for ep in range(epochs):
            opt.zero_grad()
            theta, _ = model(hesitation, staleness, edge_type, src, dst, stress)
            loss = criterion(theta.squeeze(), y_target)
            loss.backward()
            opt.step()
            losses.append(loss.item())
        return losses
    
    vqc_losses = train_loop(vqc, vqc_opt, "VQC")
    mlp_losses = train_loop(mlp, mlp_opt, "MLP")
    
    results = {
        "expressivity": {
            "vqc_final_mse": round(vqc_losses[-1], 4),
            "mlp_final_mse": round(mlp_losses[-1], 4),
            "vqc_params": sum(p.numel() for p in vqc.parameters() if p.requires_grad),
            "mlp_params": sum(p.numel() for p in mlp.parameters() if p.requires_grad),
            "conclusion": "The VQC may or may not beat the MLP on this arbitrary synthetic function, which highlights the need for careful parameter matching and expectation management."
        }
    }
    
    os.makedirs("artifacts", exist_ok=True)
    handoff_path = "artifacts/prompt_04_handoff.json"
    if os.path.exists(handoff_path):
        with open(handoff_path, "r") as f:
            data = json.load(f)
    else:
        data = {}
        
    data.update(results)
    
    with open(handoff_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Expressivity experiment completed: {results}")

if __name__ == "__main__":
    run_expressivity_experiment()
